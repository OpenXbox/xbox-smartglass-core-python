from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from http import HTTPStatus
from xbox.sg import enum
from xbox.stump import json_model as stump_schemas

from ..deps import console_exists, console_connected
from ..consolewrap import ConsoleWrap
from .. import schemas


router = APIRouter()

@router.get('/', response_model=schemas.DeviceOverviewResponse)
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
    return schemas.DeviceOverviewResponse(devices=data)


@router.get('/{liveid}/poweron', response_model=schemas.GeneralResponse)
async def poweron(liveid: str, addr: Optional[str] = None):
    await ConsoleWrap.power_on(liveid, addr=addr)
    return schemas.GeneralResponse(success=True)


"""
Require enumerated console
"""


@router.get('/{liveid}', response_model=schemas.DeviceStatusResponse)
def device_info(
    console: ConsoleWrap = Depends(console_exists)
):
    return console.status


@router.get('/{liveid}/connect', response_model=schemas.GeneralResponse)
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
        raise HTTPException(status_code=400, detail=f'error: {str(e)}')

    if state != enum.ConnectionState.Connected:
        raise HTTPException(status_code=400, detail='Connection failed')

    return schemas.GeneralResponse(success=True, details={'connection_state': state})


"""
Require connected console
"""


@router.get('/{liveid}/disconnect', response_model=schemas.GeneralResponse)
async def disconnect(
    console: ConsoleWrap = Depends(console_connected)
):
    await console.disconnect()
    return schemas.GeneralResponse(success=True)


@router.get('/{liveid}/poweroff', response_model=schemas.GeneralResponse)
async def poweroff(
    console: ConsoleWrap = Depends(console_connected)
):
    if not await console.power_off():
        raise HTTPException(status_code=400, detail='Failed to power off')

    return schemas.GeneralResponse(success=True)


@router.get('/{liveid}/console_status', response_model=schemas.ConsoleStatusResponse)
async def console_status(
    console: ConsoleWrap = Depends(console_connected)
):
    status = console.console_status
    client = app.xbl_client
    # Update Title Info
    if client and status:
        for t in status.active_titles:
            try:
                title_id = t.title_id
                resp = app.title_cache.get(title_id)
                if not resp:
                    resp = await client.titlehub.get_title_info(title_id, 'image')
                if resp.titles[0]:
                    app.title_cache[title_id] = resp
                    t.name = resp.titles[0].name
                    t.image = resp.titles[0].display_image
                    t.type = resp.titles[0].type
            except Exception:
                pass
    return status


@router.get('/{liveid}/launch/{app_id}', response_model=schemas.GeneralResponse)
async def launch_title(
    console: ConsoleWrap = Depends(console_connected),
    *,
    app_id: str
):
    await console.launch_title(app_id)
    return schemas.GeneralResponse(success=True, details={'launched': app_id})


@router.get('/{liveid}/media_status', response_model=schemas.MediaStateResponse)
def media_status(
    console: ConsoleWrap = Depends(console_connected)
):
    return console.media_status


@router.get('/{liveid}/ir', response_model=schemas.InfraredResponse)
def infrared(
    console: ConsoleWrap = Depends(console_connected)
):
    stump_config = console.stump_config

    devices = {}
    for device_config in stump_config.params:
        button_links = {}
        for button in device_config.buttons:
            button_links[button] = schemas.InfraredButton(
                url='/device/{0}/ir/{1}/{2}'.format(console.liveid, device_config.device_id, button),
                value=device_config.buttons[button]
            )

        devices[device_config.device_type] = schemas.InfraredDevice(
            device_type=device_config.device_type,
            device_brand=device_config.device_brand,
            device_model=device_config.device_model,
            device_name=device_config.device_name,
            device_id=device_config.device_id,
            buttons=button_links
        )

    return schemas.InfraredResponse(**devices)


@router.get('/{liveid}/ir/{device_id}', response_model=schemas.InfraredDevice)
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
            button_links[button] = schemas.InfraredButton(
                url='/device/{0}/ir/{1}/{2}'.format(console.liveid, device_config.device_id, button),
                value=device_config.buttons[button]
            )

        return schemas.InfraredDevice(
            device_type=device_config.device_type,
            device_brand=device_config.device_brand,
            device_model=device_config.device_model,
            device_name=device_config.device_name,
            device_id=device_config.device_id,
            buttons=button_links
        )

    raise HTTPException(status_code=400, detail=f'Device Id \'{device_id}\' not found')


@router.get('/{liveid}/ir/{device_id}/{button}', response_model=schemas.GeneralResponse)
async def infrared_send(
    console: ConsoleWrap = Depends(console_connected),
    *,
    device_id: str,
    button: str
):
    if not await console.send_stump_key(device_id, button):
        raise HTTPException(status_code=400, detail='Failed to send button')

    return schemas.GeneralResponse(success=True, details={'sent_key': button, 'device_id': device_id})


@router.get('/{liveid}/media', response_model=schemas.MediaCommandsResponse)
def media_overview(
    console: ConsoleWrap = Depends(console_connected)
):
    return schemas.MediaCommandsResponse(commands=list(console.media_commands.keys()))


@router.get('/{liveid}/media/{command}', response_model=schemas.GeneralResponse)
async def media_command(
    console: ConsoleWrap = Depends(console_connected),
    *,
    command: str
):
    cmd = console.media_commands.get(command)
    if not cmd:
        raise HTTPException(status_code=400, detail=f'Invalid command passed, command: {command}')

    await console.send_media_command(cmd)
    return schemas.GeneralResponse(success=True)


@router.get('/{liveid}/media/seek/{seek_position}', response_model=schemas.GeneralResponse)
async def media_command_seek(
    console: ConsoleWrap = Depends(console_connected),
    *,
    seek_position: int
):
    await console.send_media_command(enum.MediaControlCommand.Seek, seek_position)
    return schemas.GeneralResponse(success=True)


@router.get('/{liveid}/input', response_model=schemas.InputResponse)
def input_overview(
    console: ConsoleWrap = Depends(console_connected)
):
    return schemas.InputResponse(buttons=list(console.input_keys.keys()))


@router.get('/{liveid}/input/{button}', response_model=schemas.GeneralResponse)
async def input_send_button(
    console: ConsoleWrap = Depends(console_connected),
    *,
    button: str
):
    btn = console.input_keys.get(button)
    if not btn:
        raise HTTPException(status_code=400, detail=f'Invalid button passed, button: {button}')

    await console.send_gamepad_button(btn)
    return schemas.GeneralResponse(success=True)


@router.get('/{liveid}/stump/headend', response_model=stump_schemas.HeadendInfo)
def stump_headend_info(
    console: ConsoleWrap = Depends(console_connected)
):
    return console.headend_info


@router.get('/{liveid}/stump/livetv', response_model=stump_schemas.LiveTvInfo)
def stump_livetv_info(
    console: ConsoleWrap = Depends(console_connected)
):
    return console.livetv_info


@router.get('/{liveid}/stump/tuner_lineups', response_model=stump_schemas.TunerLineups)
def stump_tuner_lineups(
    console: ConsoleWrap = Depends(console_connected)
):
    return console.tuner_lineups


@router.get('/{liveid}/text', response_model=schemas.device.TextSessionActiveResponse)
def text_overview(
    console: ConsoleWrap = Depends(console_connected)
):
    return schemas.TextSessionActiveResponse(text_session_active=console.text_active)


@router.get('/{liveid}/text/{text}', response_model=schemas.GeneralResponse)
async def text_send(
    console: ConsoleWrap = Depends(console_connected),
    *,
    text: str
):
    await console.send_text(text)
    return schemas.GeneralResponse(success=True)


@router.get('/{liveid}/gamedvr', response_model=schemas.GeneralResponse)
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
        raise HTTPException(status_code=400, detail=f'GameDVR failed, error: {e}')

    return schemas.GeneralResponse(success=True)
