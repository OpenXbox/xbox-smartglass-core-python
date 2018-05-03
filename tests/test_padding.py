from xbox.sg.crypto import Padding, PKCS7Padding, ANSIX923Padding


def test_calculate_padding():
    align_16 = Padding.size(12, alignment=16)
    align_12 = Padding.size(12, alignment=12)
    align_10 = Padding.size(12, alignment=10)

    assert align_16 == 4
    assert align_12 == 0
    assert align_10 == 8


def test_remove_padding():
    payload = 8 * b'\x88' + b'\x00\x00\x00\x04'
    unpadded = Padding.remove(payload)

    assert len(unpadded) == 8
    assert unpadded == 8 * b'\x88'


def test_x923_add_padding():
    payload = 7 * b'\x69'
    padded_12 = ANSIX923Padding.pad(payload, alignment=12)
    padded_7 = ANSIX923Padding.pad(payload, alignment=7)
    padded_3 = ANSIX923Padding.pad(payload, alignment=3)

    assert len(padded_12) == 12
    assert len(padded_7) == 7
    assert len(padded_3) == 9
    assert padded_12 == payload + b'\x00\x00\x00\x00\x05'
    assert padded_7 == payload
    assert padded_3 == payload + b'\x00\x02'


def test_pkcs7_add_padding():
    payload = 7 * b'\x69'
    padded_12 = PKCS7Padding.pad(payload, alignment=12)
    padded_7 = PKCS7Padding.pad(payload, alignment=7)
    padded_3 = PKCS7Padding.pad(payload, alignment=3)

    assert len(padded_12) == 12
    assert len(padded_7) == 7
    assert len(padded_3) == 9
    assert padded_12 == payload + b'\x05\x05\x05\x05\x05'
    assert padded_7 == payload
    assert padded_3 == payload + b'\x02\x02'
