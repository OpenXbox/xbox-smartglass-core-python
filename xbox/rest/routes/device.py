from quart import current_app as app
from quart import request
from http import HTTPStatus
from xbox.sg import enum
from ..decorators import console_exists, console_connected
from ..consolewrap import ConsoleWrap
from . import routes


@routes.route('/device')
async def device_overview():
    addr = request.args.get('addr')
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


@routes.route('/device/<liveid>/poweron')
async def poweron(liveid):
    addr = request.args.get('addr')
    await ConsoleWrap.power_on(liveid, addr=addr)
    return app.success()


"""
Require enumerated console
"""


@routes.route('/device/<liveid>')
@console_exists
def device_info(console):
    return app.success(device=console.status)


@routes.route('/device/<liveid>/connect')
@console_exists
async def force_connect(console):
    try:
        userhash = ''
        xtoken = ''
        if app.authentication_mgr.authenticated and not request.args.get('anonymous'):
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


@routes.route('/device/<liveid>/disconnect')
@console_connected
async def disconnect(console):
    await console.disconnect()
    return app.success()


@routes.route('/device/<liveid>/poweroff')
@console_connected
async def poweroff(console):
    if not await console.power_off():
        return app.error("Failed to power off")
    else:
        return app.success()


@routes.route('/device/<liveid>/console_status')
@console_connected
def console_status(console):
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


@routes.route('/device/<liveid>/launch/<path:app_id>')
@console_connected
async def launch_title(console, app_id):
    await console.launch_title(app_id)
    return app.success(launched=app_id)


@routes.route('/device/<liveid>/media_status')
@console_connected
def media_status(console):
    return app.success(media_status=console.media_status)


@routes.route('/device/<liveid>/ir')
@console_connected
def infrared(console):
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


@routes.route('/device/<liveid>/ir/<device_id>')
@console_connected
def infrared_available_keys(console, device_id):
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


@routes.route('/device/<liveid>/ir/<device_id>/<button>')
@console_connected
async def infrared_send(console, device_id, button):
    if not await console.send_stump_key(device_id, button):
        return app.error('Failed to send button')

    return app.success(sent_key=button, device_id=device_id)


@routes.route('/device/<liveid>/media')
@console_connected
def media_overview(console):
    return app.success(commands=list(console.media_commands.keys()))


@routes.route('/device/<liveid>/media/<command>')
@console_connected
async def media_command(console, command):
    cmd = console.media_commands.get(command)
    if not cmd:
        return app.error('Invalid command passed, command: {0}'.format(command), HTTPStatus.BAD_REQUEST)

    await console.send_media_command(cmd)
    return app.success()


@routes.route('/device/<liveid>/media/seek/<int:seek_position>')
@console_connected
async def media_command_seek(console, seek_position):
    await console.send_media_command(enum.MediaControlCommand.Seek, seek_position)
    return app.success()


@routes.route('/device/<liveid>/input')
@console_connected
def input_overview(console):
    return app.success(buttons=list(console.input_keys.keys()))


@routes.route('/device/<liveid>/input/<button>')
@console_connected
async def input_send_button(console, button):
    btn = console.input_keys.get(button)
    if not btn:
        return app.error('Invalid button passed, button: {0}'.format(button), HTTPStatus.BAD_REQUEST)

    await console.send_gamepad_button(btn)
    return app.success()


@routes.route('/device/<liveid>/stump/headend')
@console_connected
def stump_headend_info(console):
    return app.success(headend_info=console.headend_info.params.dump())


@routes.route('/device/<liveid>/stump/livetv')
@console_connected
def stump_livetv_info(console):
    return app.success(livetv_info=console.livetv_info.params.dump())


@routes.route('/device/<liveid>/stump/tuner_lineups')
@console_connected
def stump_tuner_lineups(console):
    return app.success(tuner_lineups=console.tuner_lineups.params.dump())


@routes.route('/device/<liveid>/text')
@console_connected
def text_overview(console):
    return app.success(text_session_active=console.text_active)


@routes.route('/device/<liveid>/text/<text>')
@console_connected
async def text_send(console, text):
    await console.send_text(text)
    return app.success()


@routes.route('/device/<liveid>/gamedvr')
@console_connected
async def gamedvr_record(console):
    """
    Default to record last 60 seconds
    Adjust with start/end query parameter
    (delta time in seconds)
    """
    try:
        start_delta = request.args.get('start', -60)
        end_delta = request.args.get('end', 0)
        await console.dvr_record(int(start_delta), int(end_delta))
    except Exception as e:
        return app.error('GameDVR failed, error: {0}'.format(e))

    return app.success()


@routes.route('/device/<liveid>/nano')
@console_connected
def nano_overview(console):
    return app.success(nano_status=console.nano_status)


@routes.route('/device/<liveid>/nano/start')
@console_connected
async def nano_start(console):
    await console.nano_start()
    return app.success()


@routes.route('/device/<liveid>/nano/stop')
@console_connected
async def nano_stop(console):
    await console.nano_stop()
    return app.success()
