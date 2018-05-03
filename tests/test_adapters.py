import pytest
import construct
from xbox.sg.utils import adapters


@pytest.mark.skip(reason="Not Implemented")
def test_cryptotunnel():
    pass


def test_json():
    import json

    test_data = {"Z": "ABC", "A": "XYZ", "B": 23}
    bytes_data = json.dumps(test_data,
                            separators=(',', ':'),
                            sort_keys=True).encode('utf-8')
    adapter = adapters.JsonAdapter(construct.GreedyString("utf8"))

    parsed = adapter.parse(bytes_data)
    built = adapter.build(test_data)

    with pytest.raises(json.JSONDecodeError):
        adapter.parse(b'invalid data')

    with pytest.raises(TypeError):
        adapter.parse(234)

    with pytest.raises(TypeError):
        adapter.parse("string")

    with pytest.raises(TypeError):
        adapter.build(b'invalid data')

    with pytest.raises(TypeError):
        adapter.build(234)

    with pytest.raises(TypeError):
        adapter.build("string")

    assert parsed == test_data
    assert built == bytes_data


def test_uuid(uuid_dummy):
    import struct
    test_data = uuid_dummy
    uuid_string = str(test_data).upper()
    uuid_stringbytes = uuid_string.encode('utf-8')
    uuid_sgstring = struct.pack('>H', len(uuid_stringbytes)) + uuid_stringbytes + b'\x00'
    uuid_bytes = test_data.bytes

    adapter_bytes = adapters.UUIDAdapter()
    parsed_bytes = adapter_bytes.parse(uuid_bytes)
    built_bytes = adapter_bytes.build(test_data)

    adapter_string = adapters.UUIDAdapter("utf-8")
    parsed_sgstring = adapter_string.parse(uuid_sgstring)
    built_sgstring = adapter_string.build(test_data)

    adapter_invalid = adapters.UUIDAdapter("utf-invalid")

    with pytest.raises(LookupError):
        adapter_invalid.parse(uuid_sgstring)

    with pytest.raises(LookupError):
        adapter_invalid.build(test_data)

    with pytest.raises(construct.StreamError):
        adapter_bytes.parse(uuid_bytes[:-2])

    with pytest.raises(TypeError):
        adapter_bytes.parse('string, not bytes object')

    with pytest.raises(TypeError):
        adapter_bytes.build('some-string, not UUID object')

    with pytest.raises(construct.StreamError):
        adapter_string.parse(uuid_sgstring[:-3])

    with pytest.raises(TypeError):
        adapter_string.parse('string, not sgstring-bytes')

    with pytest.raises(TypeError):
        adapter_string.build('some-string, not UUID object')

    assert parsed_bytes == test_data
    assert built_bytes == uuid_bytes
    assert parsed_sgstring == test_data
    assert built_sgstring == uuid_sgstring


def test_certificate(certificate_data):
    import struct
    prefixed_data = struct.pack('>H', len(certificate_data)) + certificate_data
    certinfo = adapters.CertificateInfo(certificate_data)

    adapter = adapters.CertificateAdapter()

    parsed = adapter.parse(prefixed_data)
    built = adapter.build(certinfo)

    with pytest.raises(construct.core.StreamError):
        adapter.parse(prefixed_data[:-6])

    with pytest.raises(construct.core.StreamError):
        adapter.parse(b'\xAB' * 10)

    with pytest.raises(construct.core.StreamError):
        adapter.parse(certificate_data)

    with pytest.raises(TypeError):
        adapter.parse('string, not bytes')

    with pytest.raises(TypeError):
        adapter.parse(123)

    with pytest.raises(TypeError):
        adapter.build(b'\xAB' * 10)

    with pytest.raises(TypeError):
        adapter.build(certificate_data)

    with pytest.raises(TypeError):
        adapter.build('string, not bytes')

    with pytest.raises(TypeError):
        adapter.build(123)

    assert isinstance(parsed, adapters.CertificateInfo) is True
    assert parsed == certinfo
    assert built == prefixed_data


def test_certificateinfo(certificate_data):
    certinfo = adapters.CertificateInfo(certificate_data)

    with pytest.raises(ValueError):
        adapters.CertificateInfo(certificate_data[:-1])

    with pytest.raises(ValueError):
        adapters.CertificateInfo(b'\x23' * 10)

    with pytest.raises(TypeError):
        adapters.CertificateInfo('some string')

    with pytest.raises(TypeError):
        adapters.CertificateInfo(123)

    with pytest.raises(TypeError):
        certinfo.dump(encoding='invalid param')

    assert certinfo.dump() == certificate_data
    assert certinfo.liveid == 'FFFFFFFFFFF'
