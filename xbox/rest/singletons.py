from typing import Dict, Optional

from .schemas.auth import AuthSessionConfig

from .consolewrap import ConsoleWrap 

from xbox.webapi.authentication.manager import AuthenticationManager

authentication_manager: Optional[AuthenticationManager] = None
auth_session_configs: Dict[str, AuthSessionConfig] = dict()
console_cache: Dict[str, ConsoleWrap] = dict()
title_cache: Dict[int, object] = dict()