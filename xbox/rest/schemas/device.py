from typing import List, Dict, Optional
from pydantic import BaseModel

class Device(BaseModel):
    liveid: str

class DeviceOverviewResponse(BaseModel):
    devices: Dict[str, Device]

class ActiveTitle(BaseModel):
    title_id: str
    aum: str
    name: str
    image: str
    type: str
    has_focus: bool
    title_location: str
    product_id: str
    sandbox_id: str

class ConsoleStatusResponse(BaseModel):
    live_tv_provider: str
    kernel_version: str
    locale: str
    active_titles: Optional[List[ActiveTitle]]

class MediaStateResponse(BaseModel):
    title_id: str
    aum_id: str
    asset_id: str
    media_type: str
    sound_level: str
    enabled_commands: str
    playback_status: str
    rate: str
    position: str
    media_start: int
    media_end: int
    min_seek: int
    max_seek: int
    metadata: Optional[Dict[str, str]]

class DeviceStatusResponse(BaseModel):
    connection_state: str
    pairing_state: str
    device_status: str
    last_error: int
    authenticated_users_allowed: bool
    console_users_allowed: bool
    anonymous_connection_allowed: bool
    is_certificate_pending: bool

class TextSessionActiveResponse(BaseModel):
    text_session_active: bool

class InfraredButton(BaseModel):
    url: str
    value: str

class InfraredDevice(BaseModel):
    device_type: str
    device_brand: str
    device_model: str
    device_name: str
    device_id: str
    buttons: Dict[str, InfraredButton]

class InfraredResponse(BaseModel):
    __root__: Dict[str, InfraredDevice]

class MediaCommandsResponse(BaseModel):
    commands: List[str]

class InputResponse(BaseModel):
    buttons: List[str]
