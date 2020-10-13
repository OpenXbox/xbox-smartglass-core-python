"""
Stump enumerations
"""

from uuid import UUID
from enum import Enum


class Message(str, Enum):
    """
    Message types
    """
    ERROR = "Error"
    ENSURE_STREAMING_STARTED = "EnsureStreamingStarted"
    CONFIGURATION = "GetConfiguration"
    HEADEND_INFO = "GetHeadendInfo"
    LIVETV_INFO = "GetLiveTVInfo"
    PROGRAMM_INFO = "GetProgrammInfo"
    RECENT_CHANNELS = "GetRecentChannels"
    TUNER_LINEUPS = "GetTunerLineups"
    APPCHANNEL_DATA = "GetAppChannelData"
    APPCHANNEL_LINEUPS = "GetAppChannelLineups"
    APPCHANNEL_PROGRAM_DATA = "GetAppChannelProgramData"
    SEND_KEY = "SendKey"
    SET_CHANNEL = "SetChannel"


class Notification(str, Enum):
    """
    Notification types
    """
    STREAMING_ERROR = "StreamingError"
    CHANNEL_CHANGED = "ChannelChanged"
    CHANNELTYPE_CHANGED = "ChannelTypeChanged"
    CONFIGURATION_CHANGED = "ConfigurationChanged"
    DEVICE_UI_CHANGED = "DeviceUIChanged"
    HEADEND_CHANGED = "HeadendChanged"
    VIDEOFORMAT_CHANGED = "VideoFormatChanged"
    PROGRAM_CHANGED = "ProgrammChanged"
    TUNERSTATE_CHANGED = "TunerStateChanged"


class Source(str, Enum):
    """
    Streamingsources
    """
    HDMI = "hdmi"
    TUNER = "tuner"


class DeviceType(str, Enum):
    """
    Devicetypes
    """
    TV = "tv"
    TUNER = "tuner"
    SET_TOP_BOX = "stb"
    AV_RECEIVER = "avr"


class SourceHttpQuery(str, Enum):
    """
    Source strings used in HTTP query
    """
    HDMI = "hdmi-in"
    TUNER = "zurich"


class Input(object):
    HDMI = UUID("BA5EBA11-DEA1-4BAD-BA11-FEDDEADFAB1E")


class Quality(str, Enum):
    """
    Quality values
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BEST = "best"


class FilterType(str, Enum):
    """
    Channel-filter types
    """
    ALL = "ALL"    # No filter / Show all
    HDSD = "HDSD"  # Dont show double SD-channels
    HD = "HD"      # Only show HD Channels
