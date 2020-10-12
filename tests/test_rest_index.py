import pytest
from http import HTTPStatus


@pytest.mark.asyncio
async def test_api_overview(rest_client):
    resp = await rest_client.test_client().get('/')
    resp_json = await resp.json

    assert resp.status_code == HTTPStatus.OK
    assert resp_json['success'] is True

    assert 'endpoints' in resp_json
    assert len(resp_json['endpoints']) > 1
