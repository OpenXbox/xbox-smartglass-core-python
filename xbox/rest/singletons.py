import aiohttp
from typing import Dict, Optional

from .schemas.auth import AuthSessionConfig

from .consolewrap import ConsoleWrap 

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.api.provider.titlehub import TitleHubResponse
from xbox.webapi.authentication.manager import AuthenticationManager

http_session: Optional[aiohttp.ClientSession] = None
authentication_manager: Optional[AuthenticationManager] = None
xbl_client: Optional[XboxLiveClient] = None

auth_session_configs: Dict[str, AuthSessionConfig] = dict()

console_cache: Dict[str, ConsoleWrap] = dict()
title_cache: Dict[str, TitleHubResponse] = dict()
