from typing import Optional

from fastapi import APIRouter, Depends
from http import HTTPStatus
from xbox.sg import enum
from ..deps import console_exists, console_connected
from ..consolewrap import ConsoleWrap


router = APIRouter()

@router.get('/')
async def device_overview(addr: Optional[str] = None):
    discovered = await ConsoleWrap.discover(addr=addr)
    discovered = discovered.copy()

    liveids = [d.liveid for d in discovered]
    for i, c in enumerate(app.console_cache.values()):
        if c.liveid in liveids:
            # Refresh existing entries
            index = liveids.index(c.liveid)

            if c.device_status != discovered[index].device_status:
                app.console_cache[c.liveid] = ConsoleWrap(discovered[index])
            del discovered[index]
            del liveids[index]
        elif c.liveid not in liveids:
            # Set unresponsive consoles to Unavailable
            app.console_cache[c.liveid].console.device_status = enum.DeviceStatus.Unavailable

    # Extend by new entries
    for d in discovered:
        app.console_cache.update({d.liveid: ConsoleWrap(d)})

    # Filter for specific console when ip address query is supplied (if available)
    data = {console.liveid: console.status for console in app.console_cache.values()
            if (addr and console.status.get('address') == addr) or not addr}
    return app.success(devices=data)


@router.get('/{liveid}/poweron')
async def poweron(liveid: str, addr: Optional[str] = None):
    await ConsoleWrap.power_on(liveid, addr=addr)
    return Ok()


"""
Require enumerated console
"""


@router.get('/{liveid}')
def device_info(
    console: ConsoleWrap = Depends(console_exists)
):
    return console.status


@router.get('/{liveid}/connect')
async def force_connect(
    console: ConsoleWrap = Depends(console_exists),
    anonymous: Optional[bool] = True
):
    try:
        userhash = ''
        xtoken = ''
        if app.authentication_mgr.authenticated and not anonymous:
            userhash = app.authentication_mgr.userinfo.userhash
            xtoken = app.authentication_mgr.xsts_token.jwt
        state = await console.connect(userhash, xtoken)
    except Exception as e:
        return app.error(str(e))

    if state != enum.ConnectionState.Connected:
        return app.error('Connection failed', connection_state=state.name)

    return app.success(connection_state=state.name)


"""
Require connected console
"""


@router.get('/{liveid}/disconnect')
async def disconnect(
    console: ConsoleWrap = Depends(console_connected)
):
    await console.disconnect()
    return app.success()


@router.get('/{liveid}/poweroff')
async def poweroff(
    console: ConsoleWrap = Depends(console_connected)
):
    if not await console.power_off():
        return app.error("Failed to power off")
    else:
        return app.success()


@router.get('/{liveid}/console_status')
def console_status(
    console: ConsoleWrap = Depends(console_connected)
):
    status = console.console_status
    client = app.xbl_client
    # Update Title Info
    if client and status:
        for t in status['active_titles']:
            try:
                title_id = t['title_id']
                resp = app.title_cache.get(title_id)
                if not resp:
                    resp = client.titlehub.get_title_info(title_id, 'image').json()
                if resp['titles'][0]:
                    app.title_cache[title_id] = resp
                    t['name'] = resp['titles'][0]['name']
                    t['image'] = resp['titles'][0]['displayImage']
                    t['type'] = resp['titles'][0]['type']
            except Exception:
                pass
    return app.success(console_status=status)


@router.get('/{liveid}/launch/{app_id}')
async def launch_title(
    console: ConsoleWrap = Depends(console_connected),
    *,
    app_id: str
):
    await console.launch_title(app_id)
    return app.success(launched=app_id)


@router.get('/{liveid}/media_status')
def media_status(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(media_status=console.media_status)


@router.get('/{liveid}/ir')
def infrared(
    console: ConsoleWrap = Depends(console_connected)
):
    stump_config = console.stump_config

    devices = {}
    for device_config in stump_config.params:
        button_links = {}
        for button in device_config.buttons:
            button_links[button] = {
                'url': '/device/{0}/ir/{1}/{2}'.format(console.liveid, device_config.device_id, button),
                'value': device_config.buttons[button]
            }

        devices[device_config.device_type] = {
            'device_type': device_config.device_type,
            'device_brand': device_config.device_brand,
            'device_model': device_config.device_model,
            'device_name': device_config.device_name,
            'device_id': device_config.device_id,
            'buttons': button_links
        }

    return app.success(**devices)


@router.get('/{liveid}/ir/{device_id}')
def infrared_available_keys(
    console: ConsoleWrap = Depends(console_connected),
    *,
    device_id: str
):
    stump_config = console.stump_config
    for device_config in stump_config.params:
        if device_config.device_id != device_id:
            continue

        button_links = {}
        for button in device_config.buttons:
            button_links[button] = {
                'url': '/device/{0}/ir/{1}/{2}'.format(console.liveid, device_config.device_id, button),
                'value': device_config.buttons[button]
            }

        return app.success(
            device_type=device_config.device_type,
            device_brand=device_config.device_brand,
            device_model=device_config.device_model,
            device_name=device_config.device_name,
            device_id=device_config.device_id,
            buttons=button_links
        )

    return app.error('Device Id \'{0}\' not found'.format(device_id), HTTPStatus.BAD_REQUEST)


@router.get('/{liveid}/ir/{device_id}/{button}')
async def infrared_send(
    console: ConsoleWrap = Depends(console_connected),
    *,
    device_id: str,
    button: str
):
    if not await console.send_stump_key(device_id, button):
        return app.error('Failed to send button')

    return app.success(sent_key=button, device_id=device_id)


@router.get('/{liveid}/media')
def media_overview(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(commands=list(console.media_commands.keys()))


@router.get('/{liveid}/media/{command}')
async def media_command(
    console: ConsoleWrap = Depends(console_connected),
    *,
    command: str
):
    cmd = console.media_commands.get(command)
    if not cmd:
        return app.error('Invalid command passed, command: {0}'.format(command), HTTPStatus.BAD_REQUEST)

    await console.send_media_command(cmd)
    return app.success()


@router.get('/{liveid}/media/seek/{seek_position}')
async def media_command_seek(
    console: ConsoleWrap = Depends(console_connected),
    *,
    seek_position: int
):
    await console.send_media_command(enum.MediaControlCommand.Seek, seek_position)
    return app.success()


@router.get('/{liveid}/input')
def input_overview(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(buttons=list(console.input_keys.keys()))


@router.get('/{liveid}/input/{button}')
async def input_send_button(
    console: ConsoleWrap = Depends(console_connected),
    *,
    button: str
):
    btn = console.input_keys.get(button)
    if not btn:
        return app.error('Invalid button passed, button: {0}'.format(button), HTTPStatus.BAD_REQUEST)

    await console.send_gamepad_button(btn)
    return app.success()


@router.get('/{liveid}/stump/headend')
def stump_headend_info(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(headend_info=console.headend_info.params.dump())


@router.get('/{liveid}/stump/livetv')
def stump_livetv_info(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(livetv_info=console.livetv_info.params.dump())


@router.get('/{liveid}/stump/tuner_lineups')
def stump_tuner_lineups(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(tuner_lineups=console.tuner_lineups.params.dump())


@router.get('/{liveid}/text')
def text_overview(
    console: ConsoleWrap = Depends(console_connected)
):
    return app.success(text_session_active=console.text_active)


@router.get('/{liveid}/text/{text}')
async def text_send(
    console: ConsoleWrap = Depends(console_connected),
    *,
    text: str
):
    await console.send_text(text)
    return app.success()


@router.get('/{liveid}/gamedvr')
async def gamedvr_record(
    console: ConsoleWrap = Depends(console_connected),
    start: Optional[int] = -60,
    end: Optional[int] = 0
):
    """
    Default to record last 60 seconds
    Adjust with start/end query parameter
    (delta time in seconds)
    """
    try:
        await console.dvr_record(start, end)
    except Exception as e:
        return app.error('GameDVR failed, error: {0}'.format(e))

    return app.success()
