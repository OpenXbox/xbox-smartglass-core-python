from flask import current_app as app
from flask import request, render_template
from http import HTTPStatus
from xbox.webapi.authentication.manager import AuthenticationManager,\
    AuthenticationException, TwoFactorAuthRequired
from . import routes

@routes.route('/auth')
def authentication_overview():
    tokens = {
        'access_token': app.authentication_mgr.access_token,
        'refresh_token': app.authentication_mgr.refresh_token,
        'user_token': app.authentication_mgr.user_token,
        'xsts_token': app.authentication_mgr.xsts_token
    }

    data = {}
    for k, v in tokens.items():
        data.update({k: v.to_dict() if v else None})
    userinfo = app.authentication_mgr.userinfo.to_dict() if app.authentication_mgr.userinfo else None

    return app.success(tokens=data, userinfo=userinfo, authenticated=app.authentication_mgr.authenticated)


@routes.route('/auth/login')
def authentication_login():
    if app.authentication_mgr.authenticated:
        return render_template('auth_result.html',
                                title='Already signed in',
                                result='Already signed in',
                                message='You are already signed in, please logout first!',
                                link_path='/auth/logout',
                                link_title='Logout')
    else:
        return render_template('login.html')


@routes.route('/auth/login', methods=['POST'])
def authentication_login_post():
    is_webview = request.form.get('webview')
    email_address = request.form.get('email')
    password = request.form.get('password')

    if app.authentication_mgr.authenticated:
        return app.error('An account is already signed in.. please logout first', HTTPStatus.BAD_REQUEST)
    elif not email_address or not password:
        return app.error('No email or password parameter provided', HTTPStatus.BAD_REQUEST)

    app.authentication_mgr.email_address = email_address
    app.authentication_mgr.password = password

    try:
        app.authentication_mgr.authenticate()
        app.authentication_mgr.dump(app.token_file)
    except AuthenticationException as e:
        if is_webview:
            return render_template('auth_result.html',
                                    title='Login fail',
                                    result='Login failed',
                                    message='Error: {0}!'.format(str(e)),
                                    link_path='/auth/login',
                                    link_title='Try again')
        else:
            return app.error('Login failed! Error: {0}'.format(str(e)),
                                two_factor_required=False)

    except TwoFactorAuthRequired:
        if is_webview:
            return render_template('auth_result.html',
                                    title='Login fail',
                                    result='Login failed, 2FA required',
                                    message='Please click the following link to authenticate via OAUTH',
                                    link_path='/auth/oauth',
                                    link_title='Login via OAUTH')
        else:
            return app.error('Login failed, 2FA required!',
                                two_factor_required=True)

    except Exception as e:
        return app.error('Unhandled authentication error: {0}'.format(str(e)),
                         two_factor_required=False)

    if is_webview:
        return render_template('auth_result.html',
                                title='Login success',
                                result='Login succeeded',
                                message='Welcome {}!'.format(app.logged_in_gamertag),
                                link_path='/auth/logout',
                                link_title='Logout')
    else:
        return app.success(message='Login success', gamertag=app.logged_in_gamertag)


@routes.route('/auth/logout')
def authentication_logout():
    if app.authentication_mgr.authenticated:
        return render_template('logout.html', username=app.logged_in_gamertag)
    else:
        return render_template('auth_result.html',
                                title='Logout failed',
                                result='Logout failed',
                                message='You are currently not logged in',
                                link_path='/auth/login',
                                link_title='Login')

@routes.route('/auth/logout', methods=['POST'])
def authentication_logout_post():
    is_webview = request.form.get('webview')
    username = app.logged_in_gamertag
    app.reset_authentication()
    if is_webview:
        return render_template('auth_result.html',
                                title='Logout success',
                                result='Logout succeeded',
                                message='Goodbye {0}!'.format(username),
                                link_path='/auth/login',
                                link_title='Login')
    else:
        return app.success(message='Logout succeeded')

@routes.route('/auth/url')
def authentication_get_auth_url():
    return app.success(authorization_url=AuthenticationManager.generate_authorization_url())


@routes.route('/auth/oauth')
def authentication_oauth():
    if app.authentication_mgr.authenticated:
        return render_template('auth_result.html',
                                title='Already signed in',
                                result='Already signed in',
                                message='You are already signed in, please logout first!',
                                link_path='/auth/logout',
                                link_title='Logout')
    else:
        return render_template('login_oauth.html',
                                oauth_url=AuthenticationManager.generate_authorization_url())


@routes.route('/auth/oauth', methods=['POST'])
def authentication_oauth_post():
    is_webview = request.form.get('webview')
    app.reset_authentication()
    redirect_uri = request.form.get('redirect_uri')
    if not redirect_uri:
        return app.error('Please provide redirect_url', HTTPStatus.BAD_REQUEST)

    try:
        access, refresh = AuthenticationManager.parse_redirect_url(redirect_uri)
        app.authentication_mgr.access_token = access
        app.authentication_mgr.refresh_token = refresh
        app.authentication_mgr.authenticate(do_refresh=False)
        app.authentication_mgr.dump(app.token_file)
    except Exception as e:
        if is_webview:
            return render_template('auth_result.html',
                                    title='Login fail',
                                    result='Login failed',
                                    message='Error message: {0}'.format(str(e)),
                                    link_path='/auth/login',
                                    link_title='Try again')
        else:
            return app.error('Login failed, error: {0}'.format(str(e)))

    if is_webview:
        return render_template('auth_result.html',
                                title='Login success',
                                result='Login succeeded',
                                message='Welcome {}!'.format(app.logged_in_gamertag),
                                link_path='/auth/logout',
                                link_title='Logout')
    else:
        return app.success(message='Login success', gamertag=app.logged_in_gamertag)


@routes.route('/auth/refresh')
def authentication_refresh():
    try:
        app.authentication_mgr.authenticate(do_refresh=True)
    except Exception as e:
        return app.error(str(e))

    return app.success()


@routes.route('/auth/load')
def authentication_load_from_disk():
    try:
        app.authentication_mgr.load(app.token_file)
    except FileNotFoundError as e:
        return app.error('Failed to load tokens from \'{0}\'. Error: {1}'.format(e.filename, e.strerror), HTTPStatus.NOT_FOUND)

    return app.success()


@routes.route('/auth/store')
def authentication_store_on_disk():
    if not app.authentication_mgr.authenticated:
        return app.error('Sorry, no valid authentication for saving was found', HTTPStatus.BAD_REQUEST)

    try:
        app.authentication_mgr.dump(app.token_file)
    except Exception as e:
        return app.error('Failed to save tokens to \'{0}\'. Error: {1}'.format(app.token_file, str(e)))

    return app.success()
