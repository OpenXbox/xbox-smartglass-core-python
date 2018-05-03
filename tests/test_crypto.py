import pytest
from binascii import unhexlify
from xbox.sg.enum import PublicKeyType


def test_generate_random_iv(crypto):
    rand_iv = crypto.generate_iv()
    rand_iv_2 = crypto.generate_iv()

    assert len(rand_iv) == 16
    assert len(rand_iv_2) == 16
    assert rand_iv != rand_iv_2


def test_generate_seeded_iv(crypto):
    seed = unhexlify('000102030405060708090A0B0C0D0E0F')
    seed2 = unhexlify('000F0E0D0C0B0A090807060504030201')

    seed_iv = crypto.generate_iv(seed)
    seed_iv_dup = crypto.generate_iv(seed)
    seed_iv_2 = crypto.generate_iv(seed2)

    assert len(seed_iv) == 16
    assert seed_iv == seed_iv_dup
    assert seed_iv != seed_iv_2


def test_encrypt_decrypt(crypto):
    plaintext = b'Test String\x00\x00\x00\x00\x00'
    seed = unhexlify('000102030405060708090A0B0C0D0E0F')
    seed_iv = crypto.generate_iv(seed)
    encrypt = crypto.encrypt(seed_iv, plaintext)
    decrypt = crypto.decrypt(seed_iv, encrypt)

    assert plaintext == decrypt
    assert plaintext != encrypt


def test_hash(crypto):
    plaintext = b'Test String\x00\x00\x00\x00\x00'
    seed = unhexlify('000102030405060708090A0B0C0D0E0F')
    seed_iv = crypto.generate_iv(seed)
    encrypt = crypto.encrypt(seed_iv, plaintext)
    hash = crypto.hash(encrypt)
    hash_dup = crypto.hash(encrypt)
    verify = crypto.verify(encrypt, hash)

    assert hash == hash_dup
    assert verify is True


def test_from_bytes():
    from xbox.sg.crypto import Crypto
    public_key = unhexlify(
        '041db1e7943878b28c773228ebdcfb05b985be4a386a55f50066231360785f61b'
        '60038caf182d712d86c8a28a0e7e2733a0391b1169ef2905e4e21555b432b262d'
    )

    c1 = Crypto.from_bytes(public_key)
    c2 = Crypto.from_bytes(public_key, PublicKeyType.EC_DH_P256)

    # invalid public key type passed
    with pytest.raises(ValueError):
        Crypto.from_bytes(public_key, PublicKeyType.EC_DH_P521)
    # invalid keylength
    with pytest.raises(ValueError):
        Crypto.from_bytes(public_key[5:])
    # invalid parameter
    with pytest.raises(ValueError):
        Crypto.from_bytes(123)

    assert c1.foreign_pubkey.public_numbers().encode_point() == public_key
    assert c2.foreign_pubkey.public_numbers().encode_point() == public_key


def test_from_shared_secret():
    from xbox.sg.crypto import Crypto
    secret = unhexlify(
        '82bba514e6d19521114940bd65121af234c53654a8e67add7710b3725db44f77'
        '30ed8e3da7015a09fe0f08e9bef3853c0506327eb77c9951769d923d863a2f5e'
    )

    c = Crypto.from_shared_secret(secret)

    # invalid length
    with pytest.raises(ValueError):
        c.from_shared_secret(secret[1:])

    # invalid parameter
    with pytest.raises(ValueError):
        c.from_shared_secret(123)

    assert c._encrypt_key == unhexlify(b'82bba514e6d19521114940bd65121af2')
    assert c._iv_key == unhexlify(b'34c53654a8e67add7710b3725db44f77')
    assert c._hash_key == unhexlify(
        b'30ed8e3da7015a09fe0f08e9bef3853c0506327eb77c9951769d923d863a2f5e'
    )
