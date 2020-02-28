"""
JSON models for deserializing Stump messages
"""
from marshmallow_objects import Model, NestedModel, fields
from xbox.stump.enum import Message


class StumpJsonError(Exception):
    pass


# Root-level containers
class StumpResponse(Model):
    msgid = fields.Str()
    response = fields.Str()


class StumpError(Model):
    msgid = fields.Str()
    error = fields.Str()


class StumpNotification(Model):
    notification = fields.Str()


# Nested models
class _FoundChannel(Model):
    channelNumber = fields.Int()
    displayName = fields.Str()
    channelId = fields.Str()


class _LineupProvider(Model):
    foundChannels = NestedModel(_FoundChannel, many=True, required=True)
    cqsChannels = fields.List(fields.Str(), required=True)
    headendId = fields.UUID()


class _EnsureStreamingStarted(Model):
    currentChannelId = fields.Str()
    source = fields.Str()
    streamingPort = fields.Int()
    tunerChannelType = fields.Str()
    userCanViewChannel = fields.Str()


class _TunerLineups(Model):
    providers = NestedModel(_LineupProvider, many=True)


class _RecentChannel(Model):
    channelNum = fields.Str()  # Can be "NumberUnused" instead of int
    providerId = fields.UUID()
    channelId = fields.Str()


class _PauseBufferInfo(Model):
    Enabled = fields.Bool()
    IsDvr = fields.Bool()
    MaxBufferSize = fields.Int()
    BufferCurrent = fields.Int()
    BufferStart = fields.Int()
    BufferEnd = fields.Int()
    CurrentTime = fields.Int()
    Epoch = fields.Int()


class _LiveTvInfo(Model):
    streamingPort = fields.Int()
    inHdmiMode = fields.Bool()
    tunerChannelType = fields.Str()
    currentTunerChannelId = fields.Str()
    currentHdmiChannelId = fields.Str()
    pauseBufferInfo = NestedModel(_PauseBufferInfo)


class _HeadendProvider(Model):
    providerName = fields.Str()
    filterPreference = fields.Str()
    headendId = fields.UUID()
    source = fields.Str()
    titleId = fields.Str()
    canStream = fields.Bool()


class _HeadendInfo(Model):
    providerName = fields.Str()
    headendId = fields.UUID()
    blockExplicitContentPerShow = fields.Bool()
    dvrEnabled = fields.Bool()
    headendLocale = fields.Str()
    streamingPort = fields.Int()
    preferredProvider = fields.Str()
    providers = NestedModel(_HeadendProvider, many=True)


class _DeviceConfiguration(Model):
    device_id = fields.Str()
    device_type = fields.Str()
    device_brand = fields.Str()
    device_model = fields.Str()
    device_name = fields.Str()
    buttons = fields.Dict()


class _AppChannel(Model):
    name = fields.Str()
    id = fields.Str()


class _AppProvider(Model):
    id = fields.Str()
    providerName = fields.Str()
    titleId = fields.Str()
    primaryColor = fields.Str()
    secondaryColor = fields.Str()
    providerImageUrl = fields.Str()
    channels = NestedModel(_AppChannel, many=True)


# Stump responses
class AppChannelLineups(StumpResponse):
    params = NestedModel(_AppProvider, many=True)


class EnsureStreamingStarted(StumpResponse):
    params = NestedModel(_EnsureStreamingStarted)


class TunerLineups(StumpResponse):
    params = NestedModel(_TunerLineups)


class SendKey(StumpResponse):
    params = fields.Bool()


class RecentChannels(StumpResponse):
    params = NestedModel(_RecentChannel, many=True)


class Configuration(StumpResponse):
    params = NestedModel(_DeviceConfiguration, many=True)


class LiveTvInfo(StumpResponse):
    params = NestedModel(_LiveTvInfo)


class HeadendInfo(StumpResponse):
    params = NestedModel(_HeadendInfo)


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


def deserialize_stump_message(data):
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

        return model.load(data)
    elif notification:
        return StumpNotification.load(data)
    elif error:
        return StumpError.load(data)
