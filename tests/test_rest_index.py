from http import HTTPStatus


def test_api_overview(rest_client):
    resp = rest_client.test_client().get('/')

    assert resp.status_code == HTTPStatus.OK
    assert resp.json['success'] is True

    assert 'endpoints' in resp.json
    assert len(resp.json['endpoints']) > 1
