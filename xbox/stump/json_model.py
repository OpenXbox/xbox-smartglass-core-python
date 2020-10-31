"""
JSON models for deserializing Stump messages
"""
from typing import List, Dict, Union, Optional
from uuid import UUID
from pydantic import BaseModel
from xbox.stump.enum import Message


class StumpJsonError(Exception):
    pass


# Root-level containers
class StumpRequest(BaseModel):
    msgid: str
    request: str
    params: Optional[dict]

class StumpResponse(BaseModel):
    msgid: str
    response: str


class StumpError(BaseModel):
    msgid: str
    error: str


class StumpNotification(BaseModel):
    notification: str


# Nested models
class _FoundChannel(BaseModel):
    channelNumber: int
    displayName: str
    channelId: str


class _LineupProvider(BaseModel):
    foundChannels: List[_FoundChannel]
    cqsChannels: List[str]
    headendId: UUID


class _EnsureStreamingStarted(BaseModel):
    currentChannelId: str
    source: str
    streamingPort: int
    tunerChannelType: str
    userCanViewChannel: str


class _TunerLineups(BaseModel):
    providers: List[_LineupProvider]


class _RecentChannel(BaseModel):
    channelNum: str  # Can be "NumberUnused" instead of int
    providerId: UUID
    channelId: str


class _PauseBufferInfo(BaseModel):
    Enabled: bool
    IsDvr: bool
    MaxBufferSize: int
    BufferCurrent: int
    BufferStart: int
    BufferEnd: int
    CurrentTime: int
    Epoch: int


class _LiveTvInfo(BaseModel):
    streamingPort: Optional[int]
    inHdmiMode: bool
    tunerChannelType: Optional[str]
    currentTunerChannelId: Optional[str]
    currentHdmiChannelId: Optional[str]
    pauseBufferInfo: Optional[_PauseBufferInfo]


class _HeadendProvider(BaseModel):
    providerName: str
    filterPreference: str
    headendId: UUID
    source: str
    titleId: str
    canStream: bool


class _HeadendInfo(BaseModel):
    providerName: str
    headendId: UUID
    blockExplicitContentPerShow: bool
    dvrEnabled: bool
    headendLocale: str
    streamingPort: Optional[int]
    preferredProvider: Optional[str]
    providers: List[_HeadendProvider]


class _DeviceConfiguration(BaseModel):
    device_id: str
    device_type: str
    device_brand: Optional[str]
    device_model: Optional[str]
    device_name: Optional[str]
    buttons: Dict[str, str]


class _AppChannel(BaseModel):
    name: str
    id: str


class _AppProvider(BaseModel):
    id: str
    providerName: str
    titleId: str
    primaryColor: str
    secondaryColor: str
    providerImageUrl: Optional[str]
    channels: List[_AppChannel]


# Stump responses
class AppChannelLineups(StumpResponse):
    params: List[_AppProvider]


class EnsureStreamingStarted(StumpResponse):
    params: _EnsureStreamingStarted


class TunerLineups(StumpResponse):
    params: _TunerLineups


class SendKey(StumpResponse):
    params: bool


class RecentChannels(StumpResponse):
    params: List[_RecentChannel]


class Configuration(StumpResponse):
    params: List[_DeviceConfiguration]


class LiveTvInfo(StumpResponse):
    params: _LiveTvInfo


class HeadendInfo(StumpResponse):
    params: _HeadendInfo


response_map = {
    Message.CONFIGURATION: Configuration,
    Message.ENSURE_STREAMING_STARTED: EnsureStreamingStarted,
    Message.SEND_KEY: SendKey,
    Message.RECENT_CHANNELS: RecentChannels,
    Message.SET_CHANNEL: None,
    Message.APPCHANNEL_PROGRAM_DATA: None,
    Message.APPCHANNEL_DATA: None,
    Message.APPCHANNEL_LINEUPS: AppChannelLineups,
    Message.TUNER_LINEUPS: TunerLineups,
    Message.PROGRAMM_INFO: None,
    Message.LIVETV_INFO: LiveTvInfo,
    Message.HEADEND_INFO: HeadendInfo,
    Message.ERROR: None
}


def deserialize_stump_message(data: dict) -> Union[StumpError, StumpNotification, StumpResponse]:
    """
    Helper for deserializing JSON stump messages

    Args:
        data (dict): Stump message

    Returns:
        Model: Parsed JSON object
    """
    response = data.get('response')
    notification = data.get('notification')
    error = data.get('error')

    if response:
        response = Message(response)
        model = response_map.get(response)
        if not issubclass(model, StumpResponse):
            raise StumpJsonError('Model not of subclass StumpResponse')

        return model.parse_obj(data)
    elif notification:
        return StumpNotification.load(data)
    elif error:
        return StumpError.load(data)
