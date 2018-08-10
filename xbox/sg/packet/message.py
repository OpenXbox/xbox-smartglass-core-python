# flake8: noqa
"""
Construct containers for message header and payloads
"""
from construct import *
from xbox.sg import enum
from xbox.sg.enum import PacketType, MessageType
from xbox.sg.utils.struct import XStruct
from xbox.sg.utils.adapters import CryptoTunnel, UUIDAdapter, JsonAdapter, XSwitch, XEnum, SGString, PrefixedBytes


header = XStruct(
    'pkt_type' / Default(XEnum(Int16ub, PacketType), PacketType.Message),
    'protected_payload_length' / Default(Int16ub, 0),
    'sequence_number' / Int32ub,
    'target_participant_id' / Int32ub,
    'source_participant_id' / Int32ub,
    'flags' / BitStruct(
        'version' / Default(BitsInteger(2), 2),
        'need_ack' / Flag,
        'is_fragment' / Flag,
        'msg_type' / XEnum(BitsInteger(12), MessageType)
    ),
    'channel_id' / Int64ub
)


fragment = XStruct(
    'sequence_begin' / Int32ub,
    'sequence_end' / Int32ub,
    'data' / PrefixedBytes(Int16ub)
)


acknowledge = XStruct(
    'low_watermark' / Int32ub,
    'processed_list' / PrefixedArray(Int32ub, Int32ub),
    'rejected_list' / PrefixedArray(Int32ub, Int32ub)
)


json = XStruct(
    'text' / JsonAdapter(SGString())
)


local_join = XStruct(
    'device_type' / XEnum(Int16ub, enum.ClientType),
    'native_width' / Int16ub,
    'native_height' / Int16ub,
    'dpi_x' / Int16ub,
    'dpi_y' / Int16ub,
    'device_capabilities' / XEnum(Int64ub, enum.DeviceCapabilities),
    'client_version' / Int32ub,
    'os_major_version' / Int32ub,
    'os_minor_version' / Int32ub,
    'display_name' / SGString()
)


auxiliary_stream = XStruct(
    'connection_info_flag' / Int8ub,
    'connection_info' / If(this.connection_info_flag == 1, Struct(
        'crypto_key' / PrefixedBytes(Int16ub),
        'server_iv' / PrefixedBytes(Int16ub),
        'client_iv' / PrefixedBytes(Int16ub),
        'sign_hash' / PrefixedBytes(Int16ub),
        'endpoints' / PrefixedArray(Int16ub, Struct(
            'ip' / SGString(),
            'port' / SGString()
        ))
    ))
)


power_off = XStruct(
    'liveid' / SGString()
)


game_dvr_record = XStruct(
    'start_time_delta' / Int32sb,
    'end_time_delta' / Int32sb
)


unsnap = XStruct(
    'unk' / Bytes(1)
)


gamepad = XStruct(
    'timestamp' / Int64ub,
    'buttons' / XEnum(Int16ub, enum.GamePadButton),
    'left_trigger' / Float32b,
    'right_trigger' / Float32b,
    'left_thumbstick_x' / Float32b,
    'left_thumbstick_y' / Float32b,
    'right_thumbstick_x' / Float32b,
    'right_thumbstick_y' / Float32b
)


paired_identity_state_changed = XStruct(
    'state' / XEnum(Int16ub, enum.PairedIdentityState)
)


media_state = XStruct(
    'title_id' / Int32ub,
    'aum_id' / SGString(),
    'asset_id' / SGString(),
    'media_type' / XEnum(Int16ub, enum.MediaType),
    'sound_level' / XEnum(Int16ub, enum.SoundLevel),
    'enabled_commands' / XEnum(Int32ub, enum.MediaControlCommand),
    'playback_status' / XEnum(Int16ub, enum.MediaPlaybackStatus),
    'rate' / Float32b,
    'position' / Int64ub,
    'media_start' / Int64ub,
    'media_end' / Int64ub,
    'min_seek' / Int64ub,
    'max_seek' / Int64ub,
    'metadata' / PrefixedArray(Int16ub, Struct(
        'name' / SGString(),
        'value' / SGString()
    ))
)


media_controller_removed = XStruct(
    'title_id' / Int32ub
)


media_command_result = XStruct(
    'request_id' / Int64ub,
    'result' / Int32ub
)


media_command = XStruct(
    'request_id' / Int64ub,
    'title_id' / Int32ub,
    'command' / XEnum(Int32ub, enum.MediaControlCommand),
    'seek_position' / If(this.command == enum.MediaControlCommand.Seek, Int64ub)
)


orientation = XStruct(
    'timestamp' / Int64ub,
    'rotation_matrix_value' / Float32b,
    'w' / Float32b,
    'x' / Float32b,
    'y' / Float32b,
    'z' / Float32b
)


compass = XStruct(
    'timestamp' / Int64ub,
    'magnetic_north' / Float32b,
    'true_north' / Float32b
)


inclinometer = XStruct(
    'timestamp' / Int64ub,
    'pitch' / Float32b,
    'roll' / Float32b,
    'yaw' / Float32b
)


gyrometer = XStruct(
    'timestamp' / Int64ub,
    'angular_velocity_x' / Float32b,
    'angular_velocity_y' / Float32b,
    'angular_velocity_z' / Float32b
)


accelerometer = XStruct(
    'timestamp' / Int64ub,
    'acceleration_x' / Float32b,
    'acceleration_y' / Float32b,
    'acceleration_z' / Float32b
)


_touchpoint = XStruct(
    'touchpoint_id' / Int32ub,
    'touchpoint_action' / XEnum(Int16ub, enum.TouchAction),
    'touchpoint_x' / Int32ub,
    'touchpoint_y' / Int32ub
)


touch = XStruct(
    'touch_msg_timestamp' / Int32ub,
    'touchpoints' / PrefixedArray(Int16ub, _touchpoint)
)


disconnect = XStruct(
    'reason' / XEnum(Int32ub, enum.DisconnectReason),
    'error_code' / Int32ub
)


stop_channel = XStruct(
    'target_channel_id' / Int64ub
)


start_channel_request = XStruct(
    'channel_request_id' / Int32ub,
    'title_id' / Int32ub,
    'service' / UUIDAdapter(),
    'activity_id' / Int32ub
)


start_channel_response = XStruct(
    'channel_request_id' / Int32ub,
    'target_channel_id' / Int64ub,
    'result' / XEnum(Int32ub, enum.SGResultCode)
)


title_launch = XStruct(
    'location' / XEnum(Int16ub, enum.ActiveTitleLocation),
    'uri' / SGString()
)


system_text_done = XStruct(
    'text_session_id' / Int32ub,
    'text_version' / Int32ub,
    'flags' / Int32ub,
    'result' / XEnum(Int32ub, enum.TextResult)
)


system_text_acknowledge = XStruct(
    'text_session_id' / Int32ub,
    'text_version_ack' / Int32ub
)

_system_text_input_delta = XStruct(
    'offset' / Int32ub,
    'delete_count' / Int32ub,
    'insert_content' / SGString()
)

system_text_input = XStruct(
    'text_session_id' / Int32ub,
    'base_version' / Int32ub,
    'submitted_version' / Int32ub,
    'total_text_byte_len' / Int32ub,
    'selection_start' / Int32sb,
    'selection_length' / Int32sb,
    'flags' / Int16ub,
    'text_chunk_byte_start' / Int32ub,
    'text_chunk' / SGString(),
    'delta' / Optional(PrefixedArray(Int16ub, _system_text_input_delta))
)


title_text_selection = XStruct(
    'text_session_id' / Int64ub,
    'text_buffer_version' / Int32ub,
    'start' / Int32ub,
    'length' / Int32ub
)


title_text_input = XStruct(
    'text_session_id' / Int64ub,
    'text_buffer_version' / Int32ub,
    'result' / XEnum(Int16ub, enum.TextResult),
    'text' / SGString()
)


text_configuration = XStruct(
    'text_session_id' / Int64ub,
    'text_buffer_version' / Int32ub,
    'text_options' / XEnum(Int32ub, enum.TextOption),
    'input_scope' / XEnum(Int32ub, enum.TextInputScope),
    'max_text_length' / Int32ub,
    'locale' / SGString(),
    'prompt' / SGString()
)


_active_title = XStruct(
    'title_id' / Int32ub,
    'disposition' / BitStruct(
        'has_focus' / Flag,
        'title_location' / XEnum(BitsInteger(15), enum.ActiveTitleLocation)
    ),
    'product_id' / UUIDAdapter(),
    'sandbox_id' / UUIDAdapter(),
    'aum' / SGString()
)


console_status = XStruct(
    'live_tv_provider' / Int32ub,
    'major_version' / Int32ub,
    'minor_version' / Int32ub,
    'build_number' / Int32ub,
    'locale' / SGString(),
    'active_titles' / PrefixedArray(Int16ub, _active_title)
)


active_surface_change = XStruct(
    'surface_type' / XEnum(Int16ub, enum.ActiveSurfaceType),
    'server_tcp_port' / Int16ub,
    'server_udp_port' / Int16ub,
    'session_id' / UUIDAdapter(),
    'render_width' / Int16ub,
    'render_height' / Int16ub,
    'master_session_key' / Bytes(0x20)
)

message_structs = {
    MessageType.Ack: acknowledge,
    MessageType.Group: Pass,
    MessageType.LocalJoin: local_join,
    MessageType.StopActivity: Pass,
    MessageType.AuxilaryStream: auxiliary_stream,
    MessageType.ActiveSurfaceChange: active_surface_change,
    MessageType.Navigate: Pass,
    MessageType.Json: json,
    MessageType.Tunnel: Pass,
    MessageType.ConsoleStatus: console_status,
    MessageType.TitleTextConfiguration: text_configuration,
    MessageType.TitleTextInput: title_text_input,
    MessageType.TitleTextSelection: title_text_selection,
    MessageType.MirroringRequest: Pass,
    MessageType.TitleLaunch: title_launch,
    MessageType.StartChannelRequest: start_channel_request,
    MessageType.StartChannelResponse: start_channel_response,
    MessageType.StopChannel: stop_channel,
    MessageType.System: Pass,
    MessageType.Disconnect: disconnect,
    MessageType.TitleTouch: touch,
    MessageType.Accelerometer: accelerometer,
    MessageType.Gyrometer: gyrometer,
    MessageType.Inclinometer: inclinometer,
    MessageType.Compass: compass,
    MessageType.Orientation: orientation,
    MessageType.PairedIdentityStateChanged: paired_identity_state_changed,
    MessageType.Unsnap: unsnap,
    MessageType.GameDvrRecord: game_dvr_record,
    MessageType.PowerOff: power_off,
    MessageType.MediaControllerRemoved: media_controller_removed,
    MessageType.MediaCommand: media_command,
    MessageType.MediaCommandResult: media_command_result,
    MessageType.MediaState: media_state,
    MessageType.Gamepad: gamepad,
    MessageType.SystemTextConfiguration: text_configuration,
    MessageType.SystemTextInput: system_text_input,
    MessageType.SystemTouch: touch,
    MessageType.SystemTextAck: system_text_acknowledge,
    MessageType.SystemTextDone: system_text_done
}

struct = XStruct(
    'header' / header,
    'protected_payload' / CryptoTunnel(
        IfThenElse(this.header.flags.is_fragment, fragment,
            XSwitch(
                this.header.flags.msg_type,
                message_structs,
                Pass
            )
        )
    )
)
