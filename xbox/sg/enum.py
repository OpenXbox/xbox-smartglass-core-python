"""
Smartglass enumerations
"""

from enum import Enum, Flag


class PacketType(Enum):
    """
    Packet Types of core protocol:
    Connect*, Discovery*, PowerOnRequest -> SimpleMessage
    Message -> Message
    """
    ConnectRequest = 0xCC00
    ConnectResponse = 0xCC01
    DiscoveryRequest = 0xDD00
    DiscoveryResponse = 0xDD01
    PowerOnRequest = 0xDD02
    Message = 0xD00D


class ClientType(Enum):
    """
    Client Type

    Used in `DiscoveryRequest`, `DiscoveryResponse` and `LocalJoin`-Message.
    """
    XboxOne = 0x1
    Xbox360 = 0x2
    WindowsDesktop = 0x3
    WindowsStore = 0x4
    WindowsPhone = 0x5
    iPhone = 0x6
    iPad = 0x7
    Android = 0x8


class DeviceCapabilities(Flag):
    """
    Bitmask for client device hardware capabilities
    """
    Non = 0
    Streaming = 1
    Audio = 2
    Accelerometer = 4
    Compass = 8
    Gyrometer = 16
    Inclinometer = 32
    Orientation = 64
    All = 0xFFFFFFFFFFFFFFFF


class ConnectionResult(Enum):
    """
    Connection Result

    Used in result-field of `ConnectResponse` packet.
    """
    Success = 0x0
    Pending = 0x1
    FailureUnknown = 0x2
    FailureAnonymousConnectionsDisabled = 0x3
    FailureDeviceLimitExceeded = 0x4
    FailureSmartGlassDisabled = 0x5
    FailureUserAuthFailed = 0x6
    FailureUserSignInFailed = 0x7
    FailureUserSignInTimeOut = 0x8
    FailureUserSignInRequired = 0x9


class PublicKeyType(Enum):
    """
    Public Key Type

    Used in `ConnectRequest` packet.
    """
    EC_DH_P256 = 0x00
    EC_DH_P384 = 0x01
    EC_DH_P521 = 0x02
    Default = 0xFFFF


class AckStatus(Enum):
    """
    Acknowledgement Status

    Internally used to signalize the waiting
    caller the status of acknowledgement.
    """
    Pending = 0
    Processed = 1
    Rejected = 2


class ConnectionState(Enum):
    """
    Connection State

    Internally used by :obj:`.Console`
    """
    Disconnected = 0x0
    Connecting = 0x1
    Connected = 0x2
    Error = 0x3
    Disconnecting = 0x4
    Reconnecting = 0x5


class DeviceStatus(Enum):
    """
    Device Status

    Internally used by :obj:`.Console`
    """
    DiscoveringAvailability = 0x1
    Available = 0x2
    Unavailable = 0x3


class PrimaryDeviceFlag(Flag):
    """
    Primary Device Flag

    Used in flags of `DiscoveryResponse` packet.
    """
    Null = 0x0
    AllowConsoleUsers = 0x1
    AllowAuthenticatedUsers = 0x2
    AllowAnonymousUsers = 0x4
    CertificatePending = 0x8


class DisconnectReason(Enum):
    """
    Disconnect Reason

    Used in reason-field of `Disconnect`-Message.
    """
    Unspecified = 0x0
    Error = 0x1
    PowerOff = 0x2
    Maintenance = 0x3
    AppClose = 0x4
    SignOut = 0x5
    Reboot = 0x6
    Disabled = 0x7
    LowPower = 0x8


class PairedIdentityState(Enum):
    """
    Paired Identity State

    Used in `ConnectResponse` and `PairedIdentityStateChanged`-Message.
    """
    NotPaired = 0x0
    Paired = 0x1


class ServiceChannel(Enum):
    """
    Service Channels

    Used internally to identify actual Channel Ids.
    """
    Core = 0x0
    SystemInput = 0x1
    SystemInputTVRemote = 0x2
    SystemMedia = 0x3
    SystemText = 0x4
    SystemBroadcast = 0x5
    Ack = 0x6
    Title = 0x7


class MessageType(Enum):
    """
    Message Type

    Used in `Message`-Header.
    """
    Null = 0x0
    Ack = 0x1
    Group = 0x2
    LocalJoin = 0x3
    StopActivity = 0x5
    AuxilaryStream = 0x19
    ActiveSurfaceChange = 0x1a
    Navigate = 0x1b
    Json = 0x1c
    Tunnel = 0x1d
    ConsoleStatus = 0x1e
    TitleTextConfiguration = 0x1f
    TitleTextInput = 0x20
    TitleTextSelection = 0x21
    MirroringRequest = 0x22
    TitleLaunch = 0x23
    StartChannelRequest = 0x26
    StartChannelResponse = 0x27
    StopChannel = 0x28
    System = 0x29
    Disconnect = 0x2a
    TitleTouch = 0x2e
    Accelerometer = 0x2f
    Gyrometer = 0x30
    Inclinometer = 0x31
    Compass = 0x32
    Orientation = 0x33
    PairedIdentityStateChanged = 0x36
    Unsnap = 0x37
    GameDvrRecord = 0x38
    PowerOff = 0x39
    MediaControllerRemoved = 0xf00
    MediaCommand = 0xf01
    MediaCommandResult = 0xf02
    MediaState = 0xf03
    Gamepad = 0xf0a
    SystemTextConfiguration = 0xf2b
    SystemTextInput = 0xf2c
    SystemTouch = 0xf2e
    SystemTextAck = 0xf34
    SystemTextDone = 0xf35


class ActiveTitleLocation(Enum):
    """
    Active Title Location
    """
    Full = 0x0
    Fill = 0x1
    Snapped = 0x2
    StartView = 0x3
    SystemUI = 0x4
    Default = 0x5


class ActiveSurfaceType(Enum):
    """
    Active Surface Type

    Used in `ActiveSurfaceType`-Message.
    """
    Blank = 0x0
    Direct = 0x1
    HTML = 0x2
    TitleTextEntry = 0x3


class MediaType(Enum):
    """
    Media Type

    Used in `MediaState`-Message.
    """
    NoMedia = 0x0
    Music = 0x1
    Video = 0x2
    Image = 0x3
    Conversation = 0x4
    Game = 0x5


class MediaTransportState(Enum):
    """
    Media Transport State

    Used in `MediaState`-Message.
    """
    Invalid = 0x0
    Stopped = 0x1
    Starting = 0x2
    Playing = 0x3
    Paused = 0x4
    Buffering = 0x5


class MediaPlaybackStatus(Enum):
    """
    Media Playback Status

    Used in `MediaState`-Message.
    """
    Closed = 0x0
    Changing = 0x1
    Stopped = 0x2
    Playing = 0x3
    Paused = 0x4


class MediaControlCommand(Flag):
    """
    Media Control Command

    Used in `MediaCommand`-Message.
    """
    Null = 0x0
    Play = 0x2
    Pause = 0x4
    PlayPauseToggle = 0x8
    Stop = 0x10
    Record = 0x20
    NextTrack = 0x40
    PreviousTrack = 0x80
    FastForward = 0x100
    Rewind = 0x200
    ChannelUp = 0x400
    ChannelDown = 0x800
    Back = 0x1000
    View = 0x2000
    Menu = 0x4000
    Seek = 0x8000


class SoundLevel(Enum):
    """
    Sound Level

    Used in `MediaState`-Message.
    """
    Muted = 0x0
    Low = 0x1
    Full = 0x2


class GamePadButton(Enum):
    """
    Gamepad Button

    Used in `Gamepad`-Message.
    """
    Clear = 0x0
    Enroll = 0x1
    Nexu = 0x2
    Menu = 0x4
    View = 0x8
    PadA = 0x10
    PadB = 0x20
    PadX = 0x40
    PadY = 0x80
    DPadUp = 0x100
    DPadDown = 0x200
    DPadLeft = 0x400
    DPadRight = 0x800
    LeftShoulder = 0x1000
    RightShoulder = 0x2000
    LeftThumbStick = 0x4000
    RightThumbStick = 0x8000


class TouchAction(Enum):
    """
    Touch Action

    Used in `SystemTouch`/`TitleTouch`-Message.
    """
    Null = 0x0
    Down = 0x1
    Move = 0x2
    Up = 0x3
    Cancel = 0x4


class TextInputScope(Enum):
    """
    Text Input Scope

    Used in `TextConfiguration`-Message
    """
    Default = 0x0
    Url = 0x1
    FullFilePath = 0x2
    FileName = 0x3
    EmailUserName = 0x4
    EmailSmtpAddress = 0x5
    LogOnName = 0x6
    PersonalFullName = 0x7
    PersonalNamePrefix = 0x8
    PersonalGivenName = 0x9
    PersonalMiddleName = 0xa
    PersonalSurname = 0xb
    PersonalNameSuffix = 0xc
    PostalAddress = 0xd
    PostalCode = 0xe
    AddressStreet = 0xf
    AddressStateOrProvince = 0x10
    AddressCity = 0x11
    AddressCountryName = 0x12
    AddressCountryShortName = 0x13
    CurrencyAmountAndSymbol = 0x14
    CurrencyAmount = 0x15
    Date = 0x16
    DateMonth = 0x17
    DateDay = 0x18
    DateYear = 0x19
    DateMonthName = 0x1a
    DateDayName = 0x1b
    Digits = 0x1c
    Number = 0x1d
    OneChar = 0x1e
    Password = 0x1f
    TelephoneNumber = 0x20
    TelephoneCountryCode = 0x21
    TelephoneAreaCode = 0x22
    TelephoneLocalNumber = 0x23
    Time = 0x24
    TimeHour = 0x25
    TimeMinorSec = 0x26
    NumberFullWidth = 0x27
    AlphanumericHalfWidth = 0x28
    AlphanumericFullWidth = 0x29
    CurrencyChinese = 0x2a
    Bopomofo = 0x2b
    Hiragana = 0x2c
    KatakanaHalfWidth = 0x2d
    KatakanaFullWidth = 0x2e
    Hanja = 0x2f
    HangulHalfWidth = 0x30
    HangulFullWidth = 0x31
    Search = 0x32
    SearchTitleText = 0x33
    SearchIncremental = 0x34
    ChineseHalfWidth = 0x35
    ChineseFullWidth = 0x36
    NativeScript = 0x37
    Unknown = 0x39


class TextAction(Enum):
    """
    Text Action
    """
    Cancel = 0x0
    Accept = 0x1


class TextOption(Flag):
    """
    Text Option
    """
    Default = 0x0
    AcceptsReturn = 0x1
    Password = 0x2
    MultiLine = 0x4
    SpellCheckEnabled = 0x8
    PredictionEnabled = 0x10
    RTL = 0x20
    Dismiss = 0x4000


class TextResult(Enum):
    """
    Text Result
    """
    Cancel = 0x0
    Accept = 0x1
    Null = 0xFFFF


class HashAlgorithm(Enum):
    """
    Hash Algorithm

    Unused
    """
    SHA256 = 0x0
    SHA384 = 0x1
    SHA512 = 0x2


class AsymmetricAlgorithm(Enum):
    """
    Asymmetric Algorithm

    Unused
    """
    RSA_PKCS1_1024 = 0x0
    RSA_OAEP_1024 = 0x1
    RSA_PKCS1_2048 = 0x2
    RSA_OAEP_2048 = 0x3
    EC_DSA_P256 = 0x4
    EC_DSA_P384 = 0x5
    EC_DSA_P521 = 0x6
    EC_DH_P256 = 0x7
    EC_DH_P384 = 0x8
    EC_DH_P521 = 0x9


class SymmetricAlgorithm(Enum):
    """
    Symmetric Algorithm

    Unused
    """
    AES_CBC_128 = 0x0
    AES_CBC_192 = 0x1
    AES_CBC_256 = 0x2


class AuthError(Enum):
    """
    Authentication Error

    Unused
    """
    Null = 0x0
    DevModeNotAuthorized = 0x2
    SystemUpdateRequired = 0x3
    ContentUpdateRequired = 0x4
    EnforcementBan = 0x5
    ThirdPartyBan = 0x6
    ParentalControlsBan = 0x7
    SubscriptionNotActivated = 0x8
    BillingMaintenanceRequired = 0x9
    AccountNotCreated = 0xa
    NewTermsOfUse = 0xb
    CountryNotAuthorized = 0xc
    AgeVerificationRequired = 0xd
    Curfew = 0xe
    ChildAccountNotInFamily = 0xf
    CSVTransitionRequired = 0x10
    AccountMaintenanceRequired = 0x11
    AccountTypeNotAllowed = 0x12
    ContentIsolation = 0x13
    GamertagMustChange = 0x14
    DeviceChallengeRequired = 0x15
    SignInCountExceeded = 0x16
    RetailAccountNotAllowed = 0x17
    SandboxNotAllowed = 0x18
    UnknownUser = 0x19
    RetailContentNotAuthorized = 0x1a
    ContentNotAuthorized = 0x1b
    ExpiredDeviceToken = 0x1c
    ExpiredTitleToken = 0x1d
    ExpiredUserToken = 0x1e
    InvalidDeviceToken = 0x1f
    InvalidTitleToken = 0x20
    InvalidUserToken = 0x21
    InvalidRefreshToken = 0x22


class TokensResetReason(Enum):
    """
    Tokens Reset Reason

    Unused
    """
    AuthTicketError = 0x0
    AuthTicketChanged = 0x1
    EnvironmentChanged = 0x2
    SandboxIDChanged = 0x3


class HttpRequestMethod(Enum):
    """
    HTTP Request Method

    Unused
    """
    GET = 0x0
    POST = 0x1


class EnvironmentType(Enum):
    """
    Environment Type

    Unused
    """
    Production = 0x0
    DNet = 0x1
    Mock = 0x2
    Null = 0x3


class MetricsOrigin(Enum):
    """
    Metrics Origin

    Unused
    """
    Core = 0x1
    SDK = 0x2
    Canvas = 0x3
    App = 0x4


class SGResultCode(Enum):
    """
    Smartglass Result Code

    Unused
    """
    SG_E_SUCCESS = 0x0
    SG_E_ABORT = 0x80000004
    SG_E_ACCESS_DENIED = 0x80000005
    SG_E_FAIL = 0x80000006
    SG_E_HANDLE = 0x80000007
    SG_E_INVALID_ARG = 0x80000008
    SG_E_NO_INTERFACE = 0x80000009
    SG_E_NOT_IMPL = 0x8000000a
    SG_E_OUT_OF_MEMORY = 0x8000000b
    SG_E_POINTER = 0x8000000c
    SG_E_UNEXPECTED = 0x8000000d
    SG_E_PENDING = 0x8000000e
    SG_E_INVALID_DATA = 0x8000000f
    SG_E_CANCELED = 0x80000010
    SG_E_INVALID_STATE = 0x80000011
    SG_E_NOT_FOUND = 0x80000012
    SG_E_NO_MORE_CAPACITY = 0x80000013
    SG_E_FAILED_TO_START_THREAD = 0x80000014
    SG_E_MESSAGE_EXPIRED = 0x80000015
    SG_E_TIMED_OUT = 0x80000016
    SG_E_NOT_INITIALIZED = 0x80000017
    SG_E_JSON_LENGTH_EXCEEDED = 0x80000018
    SG_E_MESSAGE_LENGTH_EXCEEDED = 0x80000019
    SG_E_INVALID_CONFIGURATION = 0x8000001a
    SG_E_EXPIRED_CONFIGURATION = 0x8000001b
    SG_E_AUTH_REQUIRED = 0x8000001d
    SG_E_TIMED_OUT_PRESENCE = 0x8000001e
    SG_E_TIMED_OUT_CONNECT = 0x8000001f
    SG_E_SOCKET_ERROR = 0x80010001
    SG_E_HTTP_ERROR = 0x80020001
    SG_E_CANCEL_SHUTDOWN = 0x80020002
    SG_E_HTTP_STATUS = 0x80020003
    SG_E_UNEXPECTED_CRYPTO_ERROR = 0x80030001
    SG_E_INVALID_CRYPT_ARG = 0x80030002
    SG_E_CRYPTO_INVALID_SIGNATURE = 0x80030003
    SG_E_INVALID_CERTIFICATE = 0x80030004
    SG_E_CHANNEL_REQUEST_UNKNOWN_ERROR = 0x80040105
    SG_E_FAILED_TO_JOIN = 0x80060001
    SG_E_ALREADY_CONNECTED = 0x80060002
    SG_E_NOT_CONNECTED = 0x80060003
    SG_E_CONSOLE_NOT_RESPONDING = 0x80060004
    SG_E_CONSOLE_DISCONNECTING = 0x80060005
    SG_E_BIG_ENDIAN_STREAM_STRING_NOT_TERMINATED = 0x80070001
    SG_E_CHANNEL_ALREADY_STARTED = 0x80080001
    SG_E_CHANNEL_FAILED_TO_START = 0x80080002
    SG_E_MAXIMUM_CHANNELS_STARTED = 0x80080003
    SG_E_JNI_CLASS_NOT_FOUND = 0x80090001
    SG_E_JNI_METHOD_NOT_FOUND = 0x80090002
    SG_E_JNI_RUNTIME_ERROR = 0x80090003
