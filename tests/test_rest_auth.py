import pytest
from http import HTTPStatus


@pytest.mark.asyncio
async def test_auth_overview(rest_client):
    resp = await rest_client.test_client().get('/auth')
    json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert json is not None

    assert 'success' in json
    assert 'authenticated' in json
    assert 'tokens' in json
    assert 'userinfo' in json

    assert 'access_token' in json['tokens']
    assert 'refresh_token' in json['tokens']
    assert 'user_token' in json['tokens']
    assert 'xsts_token' in json['tokens']

    assert json['success'] is True


@pytest.mark.asyncio
async def test_auth_login_get(rest_client):
    resp = await rest_client.test_client().get('/auth/login')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json is None
    assert b'Authenticate with Windows Live' in resp.data


@pytest.mark.asyncio
async def test_auth_login_post_no_params(rest_client):
    # No post params
    resp = await rest_client.test_client().post('/auth/login')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp_json['success'] is False
    assert resp_json['message'] == 'No email or password parameter provided'


@pytest.mark.asyncio
async def test_auth_login_post_invalid_credentials(rest_client):
    resp = await rest_client.test_client().post('/auth/login',
                                                data={'email': 'foo@bar.com', 'password': '123'})
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_json['success'] is False
    assert 'Login failed' in resp_json['message']
    assert resp_json['two_factor_required'] is False


@pytest.mark.asyncio
async def test_auth_login_post_webview_invalid_credentials(rest_client):
    resp = await rest_client.test_client().post(
        '/auth/login',
        data={
            'webview': True, 'email': 'foo@bar.com',
            'password': '123'
        }
    )
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json is None
    assert b'Login failed' in resp.data


@pytest.mark.asyncio
async def test_auth_logout_get_not_logged_in(rest_client):
    resp = await rest_client.test_client().get('/auth/logout')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json is None
    assert b'currently not logged in' in resp.data


@pytest.mark.asyncio
async def test_auth_logout_post(rest_client):
    resp = await rest_client.test_client().post('/auth/logout')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json['success'] is True
    assert resp_json['message'] == 'Logout succeeded'


@pytest.mark.asyncio
async def test_auth_logout_post_webview(rest_client):
    resp = await rest_client.test_client().post('/auth/logout', data={'webview': True})
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json is None
    assert b'Logout succeeded' in resp.data


@pytest.mark.asyncio
async def test_auth_url(rest_client):
    resp = await rest_client.test_client().get('/auth/url')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json['success'] is True
    assert resp_json['authorization_url'] is not None
    assert resp_json['authorization_url'].startswith('https://login.live.com/oauth20_authorize.srf')


@pytest.mark.asyncio
async def test_auth_oauth_get(rest_client):
    resp = await rest_client.test_client().get('/auth/oauth')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json is None
    assert b'Login via OAUTH' in resp.data


@pytest.mark.asyncio
async def test_auth_oauth_post_no_params(rest_client):
    resp = await rest_client.test_client().post('/auth/oauth')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp_json['success'] is False
    assert resp_json['message'] == 'Please provide redirect_url'


@pytest.mark.asyncio
async def test_auth_oauth_post_no_params_webview(rest_client):
    resp = await rest_client.test_client().post('/auth/oauth', data={'webview': True})
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp_json['success'] is False
    assert resp_json['message'] == 'Please provide redirect_url'


@pytest.mark.asyncio
async def test_auth_oauth_post_invalid_params(rest_client):
    resp = await rest_client.test_client().post('/auth/oauth', data={'redirect_uri': 'hxxxp:/invalid'})
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_json['success'] is False
    assert resp_json['message'].startswith('Login failed')


@pytest.mark.asyncio
async def test_auth_oauth_post_invalid_params_webview(rest_client):
    resp = await rest_client.test_client().post(
        '/auth/oauth',
        data={
            'webview': True,
            'redirect_uri': 'hxxxp:/invalid'
        }
    )

    assert resp.status_code == HTTPStatus.OK
    assert b'Login failed' in resp.data
