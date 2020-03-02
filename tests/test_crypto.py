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


def test_from_bytes(public_key_bytes, public_key):
    from xbox.sg.crypto import Crypto
    c1 = Crypto.from_bytes(public_key_bytes)
    c2 = Crypto.from_bytes(public_key_bytes, PublicKeyType.EC_DH_P256)

    # invalid public key type passed
    with pytest.raises(ValueError):
        Crypto.from_bytes(public_key_bytes, PublicKeyType.EC_DH_P521)
    # invalid keylength
    with pytest.raises(ValueError):
        Crypto.from_bytes(public_key_bytes[5:])
    # invalid parameter
    with pytest.raises(ValueError):
        Crypto.from_bytes(123)

    assert c1.foreign_pubkey.public_numbers() == public_key.public_numbers()
    assert c2.foreign_pubkey.public_numbers() == public_key.public_numbers()


def test_from_shared_secret(shared_secret_bytes):
    from xbox.sg.crypto import Crypto
    c = Crypto.from_shared_secret(shared_secret_bytes)

    # invalid length
    with pytest.raises(ValueError):
        c.from_shared_secret(shared_secret_bytes[1:])

    # invalid parameter
    with pytest.raises(ValueError):
        c.from_shared_secret(123)

    assert c._encrypt_key == unhexlify(b'82bba514e6d19521114940bd65121af2')
    assert c._iv_key == unhexlify(b'34c53654a8e67add7710b3725db44f77')
    assert c._hash_key == unhexlify(
        b'30ed8e3da7015a09fe0f08e9bef3853c0506327eb77c9951769d923d863a2f5e'
    )
