import pytest
from xbox.stump import json_model
from xbox.stump.enum import Message


def test_stump_response(stump_json):
    data = stump_json['response_recent_channels']
    msg = json_model.deserialize_stump_message(data)

    assert msg.msgid == 'xV5X1YCB.16'
    assert Message(msg.response) == Message.RECENT_CHANNELS
    assert isinstance(msg.params, list)


def test_tuner_lineups(stump_json):
    data = stump_json['response_tuner_lineups']
    msg = json_model.deserialize_stump_message(data)

    assert len(msg.params.providers) == 1
    provider = msg.params.providers[0]

    assert len(provider.foundChannels) == 19
    found_channel = provider.foundChannels[0]
    assert found_channel.channelNumber == 0
    assert found_channel.displayName == 'Das Erste HD'
    assert found_channel.channelId == '000021146A000301'

    assert len(provider.cqsChannels) == 7
    assert provider.cqsChannels[0] == '178442d3-2b13-e02b-9747-a3d4ebebcf62_PHOENIHD_23'

    assert str(provider.headendId) == '0a7fb88a-960b-c2e3-9975-7c86c5fa6c49'


def test_recent_channels(stump_json):
    data = stump_json['response_recent_channels']
    msg = json_model.deserialize_stump_message(data)

    assert len(msg.params) == 0
    # assert msg.params[0].channelNum == ''
    # assert msg.params[0].providerId == ''
    # assert msg.params[0].channelId == ''


def test_livetv_info(stump_json):
    data = stump_json['response_livetv_info']
    msg = json_model.deserialize_stump_message(data)

    assert msg.params.streamingPort == 10242
    assert msg.params.inHdmiMode is False
    assert msg.params.tunerChannelType == 'televisionChannel'
    assert msg.params.currentTunerChannelId == 'bb1ca492-232b-adfe-1f39-d010eabf179e_MSAHD_16'
    assert msg.params.currentHdmiChannelId == '731cd976-c1e9-6b95-4799-e6757d02cab1_3SATHD_1'
    assert msg.params.pauseBufferInfo is not None
    assert msg.params.pauseBufferInfo.Enabled is True
    assert msg.params.pauseBufferInfo.IsDvr is False
    assert msg.params.pauseBufferInfo.MaxBufferSize == 18000000000
    assert msg.params.pauseBufferInfo.BufferCurrent == 131688132168080320
    assert msg.params.pauseBufferInfo.BufferStart == 131688132168080320
    assert msg.params.pauseBufferInfo.BufferEnd == 131688151636700238
    assert msg.params.pauseBufferInfo.CurrentTime == 131688151636836518
    assert msg.params.pauseBufferInfo.Epoch == 0


def test_headend_info(stump_json):
    data = stump_json['response_headend_info']
    msg = json_model.deserialize_stump_message(data)

    assert msg.params.providerName == 'Sky Deutschland'
    assert str(msg.params.headendId) == '516b9ea7-5292-97ec-e7d4-f843fab6d392'
    assert msg.params.blockExplicitContentPerShow is False
    assert msg.params.dvrEnabled is False
    assert msg.params.headendLocale == 'de-DE'
    assert msg.params.streamingPort == 10242
    assert msg.params.preferredProvider == '29045393'

    assert len(msg.params.providers) == 2
    provider = msg.params.providers[0]
    assert provider.providerName == 'Sky Deutschland'
    assert provider.filterPreference == 'ALL'
    assert str(provider.headendId) == '516b9ea7-5292-97ec-e7d4-f843fab6d392'
    assert provider.source == 'hdmi'
    assert provider.titleId == '162615AD'
    assert provider.canStream is False


def test_configuration(stump_json):
    data = stump_json['response_configuration']
    msg = json_model.deserialize_stump_message(data)

    assert len(msg.params) == 4
    device_config = msg.params[0]
    assert device_config.device_brand == 'Samsung'
    assert device_config.device_id == '0'
    assert device_config.device_type == 'tv'
    assert isinstance(device_config.buttons, dict) is True


@pytest.mark.skip
def test_ensure_streaming_started(stump_json):
    data = stump_json['response_ensure_streaming_started']
    msg = json_model.deserialize_stump_message(data)

    assert msg.params.currentChannelId == ''
    assert msg.params.source == ''
    assert msg.params.streamingPort == 0
    assert msg.params.tunerChannelType == ''
    assert msg.params.userCanViewChannel == ''


def test_app_channel_lineups(stump_json):
    data = stump_json['response_appchannel_lineups']
    msg = json_model.deserialize_stump_message(data)

    assert len(msg.params) == 4
    provider = msg.params[0]
    assert provider.id == 'LiveTvHdmiProvider'
    assert provider.providerName == 'OneGuide'
    assert provider.titleId == '00000000'
    assert provider.primaryColor == 'ff107c10'
    assert provider.secondaryColor == 'ffebebeb'
    assert len(provider.channels) == 0
    # channel = provider.channels[0]
    # assert channel.name == ''
    # assert channel.id == ''


def test_send_key(stump_json):
    data = stump_json['response_sendkey']
    msg = json_model.deserialize_stump_message(data)

    assert msg.params is True
