from typing import List
from pydantic import BaseModel
from xbox.webapi.authentication.manager import AuthenticationManager

from xbox.webapi.authentication.models import OAuth2TokenResponse, XSTSResponse

class AuthSessionConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]

class AuthenticationStatus(BaseModel):
    oauth: OAuth2TokenResponse
    xsts: XSTSResponse
    session_config: AuthSessionConfig
