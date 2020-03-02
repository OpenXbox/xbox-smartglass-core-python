from flask import Flask, jsonify
from http import HTTPStatus
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.api.client import XboxLiveClient
from .routes import routes


class SmartGlassFlaskApp(Flask):
    def __init__(self, name):
        super(SmartGlassFlaskApp, self).__init__(name)

        self.console_cache = {}
        self.title_cache = {}
        self.authentication_mgr = AuthenticationManager()
        self.token_file = None
        self._xbl_client = None

    @property
    def smartglass_packetnames(self):
        return [
            'xbox-smartglass-core',
            'xbox-smartglass-nano',
            'xbox-webapi'
        ]

    @property
    def xbl_client(self):
        if self.authentication_mgr.authenticated:
            self._xbl_client = XboxLiveClient(
                userhash=self.authentication_mgr.userinfo.userhash,
                auth_token=self.authentication_mgr.xsts_token.jwt,
                xuid=self.authentication_mgr.userinfo.xuid
            )
        return self._xbl_client

    @property
    def logged_in_gamertag(self):
        return self.authentication_mgr.userinfo.gamertag if self.authentication_mgr.userinfo else '<UNKNOWN>'

    def reset_authentication(self):
        self.authentication_mgr = AuthenticationManager()

    def error(self, message, code=HTTPStatus.INTERNAL_SERVER_ERROR, **kwargs):
        ret = {
            'success': False,
            'message': message
        }
        if kwargs:
            ret.update(kwargs)
        self.logger.error(str(ret))
        return jsonify(ret), code

    @staticmethod
    def success(**kwargs):
        ret = {'success': True}
        if kwargs:
            ret.update(kwargs)
        return jsonify(ret)


app = SmartGlassFlaskApp(__name__)
app.register_blueprint(routes)
