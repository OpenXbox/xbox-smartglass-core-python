from http import HTTPStatus


def test_device_overview(rest_client):
    resp = rest_client.test_client().get('/device')

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['success'] is True


def test_device_poweron(rest_client, console_liveid):
    resp = rest_client.test_client().get('/device/{0}/poweron'.format(console_liveid))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['success'] is True


def test_device_info():
    pass


def test_connect():
    pass


def test_disconnect():
    pass


def test_poweroff():
    pass


def test_launch_title():
    pass


def test_infrared():
    pass


def test_infrared_available_keys():
    pass


def test_infrared_send():
    pass


def test_media_overview():
    pass


def test_media_command():
    pass


def test_media_command_seek():
    pass


def test_input_overview():
    pass


def test_input_send_button():
    pass


def test_stump_headend_info():
    pass


def test_stump_livetv_info():
    pass


def test_stump_tuner_lineups():
    pass


def test_text_overview():
    pass


def test_text_send():
    pass


def test_media_status(rest_client_connected_media_console_status, console_liveid):
    client = rest_client_connected_media_console_status
    resp = client.test_client().get('/device/{0}/media_status'.format(console_liveid))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['success'] is True
    assert resp.json['media_status'] is not None
    media_status = resp.json['media_status']

    assert media_status['title_id'] == 274278798
    assert media_status['aum_id'] == 'AIVDE_s9eep9cpjhg6g!App'
    assert media_status['asset_id'] == ''
    assert media_status['media_type'] == 'Video'
    assert media_status['sound_level'] == 'Full'
    assert media_status['enabled_commands'] == 6
    assert media_status['playback_status'] == 'Playing'
    assert media_status['rate'] == 1.00
    assert media_status['position'] == 0
    assert media_status['media_start'] == 0
    assert media_status['media_end'] == 0
    assert media_status['min_seek'] == 0
    assert media_status['max_seek'] == 0
    assert media_status['metadata'] is not None
    metadata = media_status['metadata']

    assert len(metadata) == 2
    assert 'title' in metadata
    assert 'subtitle' in metadata
    assert metadata['title'] == 'Some Movietitle'
    assert metadata['subtitle'] == ''


def test_console_status(rest_client_connected_media_console_status, console_liveid):
    client = rest_client_connected_media_console_status
    resp = client.test_client().get('/device/{0}/console_status'.format(console_liveid))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['success'] is True
    assert resp.json['console_status'] is not None
    status = resp.json['console_status']

    assert status['kernel_version'] == '10.0.14393'
    assert status['live_tv_provider'] == 0
    assert status['locale'] == 'en-US'
    assert status['active_titles'] is not None
    assert len(status['active_titles']) == 1
    active_title = status['active_titles'][0]

    assert active_title['title_id'] == 714681658
    assert active_title['aum'] == 'AIVDE_s9eep9cpjhg6g!App'
    assert active_title['name'] == 'AIVDE_s9eep9cpjhg6g!App'
    assert active_title['image'] is None
    assert active_title['type'] is None
    assert active_title['has_focus'] is True
    assert active_title['title_location'] == 'StartView'
    assert active_title['product_id'] == '00000000-0000-0000-0000-000000000000'
    assert active_title['sandbox_id'] == '00000000-0000-0000-0000-000000000000'
