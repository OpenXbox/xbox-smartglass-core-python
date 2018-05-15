"""
Constant values used by SmartGlass
"""
from uuid import UUID

from xbox.sg.enum import ClientType, DeviceCapabilities


class AndroidClientInfo(object):
    """
    Client Info for Android device (tablet). Used for LocalJoin messages
    """
    DeviceType = ClientType.Android
    # Resolution is portrait mode
    NativeWidth = 720
    NativeHeight = 1280
    DpiX = 160
    DpiY = 160
    DeviceCapabilities = DeviceCapabilities.All
    ClientVersion = 151117100  # v2.4.1511.17100-Beta
    OSMajor = 22  # Android 5.1.1 - API Version 22
    OSMinor = 0
    DisplayName = "com.microsoft.xboxone.smartglass.beta"


class WindowsClientInfo(object):
    """
    Client Info for Windows device, used for LocalJoin messages
    """
    DeviceType = ClientType.WindowsStore
    NativeWidth = 1080
    NativeHeight = 1920
    DpiX = 96
    DpiY = 96
    DeviceCapabilities = DeviceCapabilities.All
    ClientVersion = 39
    OSMajor = 6
    OSMinor = 2
    DisplayName = "SmartGlass-PC"


class MessageTarget(object):
    """
    UUIDs for all ServiceChannels
    """
    SystemInputUUID = UUID("fa20b8ca-66fb-46e0-adb60b978a59d35f")
    SystemInputTVRemoteUUID = UUID("d451e3b3-60bb-4c71-b3dbf994b1aca3a7")
    SystemMediaUUID = UUID("48a9ca24-eb6d-4e12-8c43d57469edd3cd")
    SystemTextUUID = UUID("7af3e6a2-488b-40cb-a93179c04b7da3a0")
    SystemBroadcastUUID = UUID("b6a117d8-f5e2-45d7-862e8fd8e3156476")
    TitleUUID = UUID('00000000-0000-0000-0000-000000000000')


class XboxOneGuid(object):
    """
    System level GUIDs
    """
    BROWSER = "9c7e0f20-78fb-4ea7-a8bd-cf9d78059a08"
    MUSIC = "6D96DEDC-F3C9-43F8-89E3-0C95BF76AD2A"
    VIDEO = "a489d977-8a87-4983-8df6-facea1ad6d93"


class TitleId(object):
    """
    System level Title Ids
    """
    AVATAR_EDITOR_TITLE_ID = 1481443281
    BROWSER_TITLE_ID = 1481115776
    DASH_TITLE_ID = 4294838225
    BLUERAY_TITLE_ID = 1783797709
    CONSOLE_UPDATE_APP_TITLE_ID = -1
    HOME_TITLE_ID = 714681658
    IE_TITLE_ID = 1032557327
    LIVETV_TITLE_ID = 371594669
    MUSIC_TITLE_ID = 419416564
    ONEGUIDE_TITLE_ID = 2055214557
    OOBE_APP_TITLE_ID = 951105730
    SNAP_AN_APP_TITLE_ID = 1783889234
    STORE_APP_TITLE_ID = 1407783715
    VIDEO_TITLE_ID = 1030770725
    ZUNE_TITLE_ID = 1481115739
