"""
Cryptography portion used for sending Smartglass message

Depending on the foreign public key type, the following Elliptic curves
can be used:

* Prime 256R1
* Prime 384R1
* Prime 521R1

1. On Discovery, the console responds with a DiscoveryResponse
   including a certificate, this certificate holds the console's
   `public key`.
2. The Client generates appropriate `elliptic curve` and derives the
   `shared secret` using `console's public key`
3. The `shared secret` is salted via 2x hashes, see `kdf_salts`
4. The `salted shared secret` is hashed using `SHA-512`
5. The `salted & hashed shared secret` is split into the following
   individual keys:

    * bytes  0-16: Encryption key (AES 128-CBC)
    * bytes 16-32: Initialization Vector key
    * bytes 32-64: Hashing key (HMAC SHA-256)

6. The resulting `public key` from this :class:`Crypto` context is
   sent with the ConnectRequest message to the console
"""
import os
import hmac
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from xbox.sg.enum import PublicKeyType
from binascii import unhexlify


CURVE_MAP = {
    PublicKeyType.EC_DH_P256: ec.SECP256R1,
    PublicKeyType.EC_DH_P384: ec.SECP384R1,
    PublicKeyType.EC_DH_P521: ec.SECP521R1
}


PUBLIC_KEY_TYPE_MAP = {v: k for k, v in CURVE_MAP.items()}


class SaltType(object):
    """
    Define whether Salt is pre- or appended
    """
    Prepend = 1
    Append = 2


class Salt(object):
    def __init__(self, value, salt_type=SaltType.Prepend):
        """
        Handle salting of ECDH shared secret

        Args:
            value (bytes): Salting bytes
            salt_type (:obj:`SaltType`): Salt Type
        """
        self.value = value
        self.type = salt_type

    def apply(self, data):
        """
        Appends or prepends salt bytes to data

        Args:
            data (bytes): Data to be salted

        Returns:
            bytes: Salted data
        """
        if self.type == SaltType.Prepend:
            return self.value + data
        if self.type == SaltType.Append:
            return data + self.value
        raise ValueError("Unknown salt type: " + str(self.type))


class Crypto(object):
    _backend = default_backend()

    _kdf_salts = (
        Salt(unhexlify('D637F1AAE2F0418C'), SaltType.Prepend),
        Salt(unhexlify('A8F81A574E228AB7'), SaltType.Append)
    )

    def __init__(self, foreign_public_key, privkey=None, pubkey=None):
        """
        Initialize Crypto context via the foreign public key of the console.
        The public key is part of the console certificate.

        Args:
            foreign_public_key (:obj:`ec.EllipticCurvePublicKey`):
                The console's public key
            privkey (:obj:`ec.EllipticCurvePrivateKey`): Optional private key
            pubkey (:obj:`ec.EllipticCurvePublicKey`): Optional public key
        """

        if not isinstance(foreign_public_key, ec.EllipticCurvePublicKey):
            raise ValueError("Unsupported public key format, \
                expected EllipticCurvePublicKey")

        if privkey and not isinstance(privkey, ec.EllipticCurvePrivateKey):
            raise ValueError("Unsupported private key format, \
                expected EllipticCurvePrivateKey")
        elif not privkey:
            privkey = ec.generate_private_key(
                foreign_public_key.curve, self._backend
            )

        if pubkey and not isinstance(pubkey, ec.EllipticCurvePublicKey):
            raise ValueError("Unsupported public key format, \
                expected EllipticCurvePublicKey")
        elif not pubkey:
            self.pubkey = privkey.public_key()
        else:
            self.pubkey = pubkey

        secret = privkey.exchange(ec.ECDH(), foreign_public_key)
        salted_secret = secret
        for salt in self._kdf_salts:
            salted_secret = salt.apply(salted_secret)

        self._expanded_secret = hashlib.sha512(salted_secret).digest()
        self._encrypt_key = self._expanded_secret[:16]
        self._iv_key = self._expanded_secret[16:32]
        self._hash_key = self._expanded_secret[32:]

        self._pubkey_type = PUBLIC_KEY_TYPE_MAP[type(self.pubkey.curve)]
        self._pubkey_bytes = self.pubkey.public_bytes(
            format=PublicFormat.UncompressedPoint,
            encoding=Encoding.X962)[1:]
        self._foreign_pubkey = foreign_public_key

    @property
    def shared_secret(self):
        """
        Shared secret

        Returns:
            bytes: Shared secret
        """
        return self._expanded_secret

    @property
    def pubkey_type(self):
        """
        Public Key Type aka. keystrength

        Returns:
            :obj:`.PublicKeyType`: Public Key Type

        """
        return self._pubkey_type

    @property
    def pubkey_bytes(self):
        """
        Public Key Bytes (minus the first identifier byte!)

        Returns:
            bytes: Public key
        """
        return self._pubkey_bytes

    @property
    def foreign_pubkey(self):
        """
        Foreign key that was used to generate this crypto context

        Returns:
            :obj:`ec.EllipticCurvePublicKey`: Console's public key
        """
        return self._foreign_pubkey

    @classmethod
    def from_bytes(cls, foreign_public_key, public_key_type=None):
        """
        Initialize Crypto context with foreign public key in
        bytes / hexstring format.

        Args:
            foreign_public_key (bytes): Console's public key
            public_key_type (:obj:`.PublicKeyType`): Public Key Type

        Returns:
            :obj:`.Crypto`: Instance
        """

        if not isinstance(foreign_public_key, bytes):
            raise ValueError("Unsupported foreign public key format, \
                expected bytes")

        if public_key_type is None:
            keylen = len(foreign_public_key)
            if keylen == 0x41:
                public_key_type = PublicKeyType.EC_DH_P256
            elif keylen == 0x61:
                public_key_type = PublicKeyType.EC_DH_P384
            elif keylen == 0x85:
                public_key_type = PublicKeyType.EC_DH_P521
            else:
                raise ValueError("Invalid public keylength")

        curve = CURVE_MAP[public_key_type]
        foreign_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            curve(), foreign_public_key
        )
        return cls(foreign_public_key)

    @classmethod
    def from_shared_secret(cls, shared_secret):
        """
        Set up crypto context with shared secret

        Args:
            shared_secret (bytes): The shared secret

        Returns:
            :obj:`.Crypto`: Instance
        """
        if not isinstance(shared_secret, bytes):
            raise ValueError("Unsupported shared secret format, \
                expected bytes")
        elif len(shared_secret) != 64:
            raise ValueError("Unsupported shared secret length, \
                expected 64 bytes")

        # We need a dummy foreign key
        dummy_key = unhexlify(
            '041db1e7943878b28c773228ebdcfb05b985be4a386a55f50066231360785f61b'
            '60038caf182d712d86c8a28a0e7e2733a0391b1169ef2905e4e21555b432b262d'
        )
        ctx = cls.from_bytes(dummy_key)
        # Overwriting shared secret
        ctx._encrypt_key = shared_secret[:16]
        ctx._iv_key = shared_secret[16:32]
        ctx._hash_key = shared_secret[32:]
        return ctx

    def generate_iv(self, seed=None):
        """
        Generates an IV to be used in encryption/decryption

        Args:
            seed (bytes): An optional IV seed

        Returns:
            bytes: Initialization Vector
        """
        if seed:
            return self._encrypt(key=self._iv_key, iv=None, data=seed)
        return os.urandom(16)

    def encrypt(self, iv, plaintext):
        """
        Encrypts plaintext with AES-128-CBC

        No padding is added here, data has to be aligned to
        block size (16 bytes).

        Args:
            iv (bytes): The IV to use. None where no IV is used.
            plaintext (bytes): The plaintext to encrypt.

        Returns:
            bytes: Encrypted Data
        """
        return Crypto._encrypt(self._encrypt_key, iv, plaintext)

    def decrypt(self, iv, ciphertext):
        """
        Decrypts ciphertext

        No padding is removed here.

        Args:
            iv (bytes): The IV to use. None where no IV is used.
            ciphertext (bytes): The hex representation of a ciphertext
                                to be decrypted

        Returns:
            bytes: Decrypted data
        """
        return Crypto._decrypt(self._encrypt_key, iv, ciphertext)

    def hash(self, data):
        """
        Securely hashes data with HMAC SHA-256

        Args:
            data (bytes): The data to securely hash.

        Returns:
            bytes: Hashed data
        """
        return Crypto._secure_hash(self._hash_key, data)

    def verify(self, data, secure_hash):
        """
        Verifies that the given data generates the given secure_hash

        Args:
            data (bytes): The data to validate.
            secure_hash (bytes): The secure hash to validate against.

        Returns:
            bool: True on success, False otherwise
        """
        return secure_hash == self.hash(data)

    @staticmethod
    def _secure_hash(key, data):
        return hmac.new(key, data, hashlib.sha256).digest()

    @staticmethod
    def _encrypt(key, iv, data):
        return Crypto._crypt(key=key, iv=iv, encrypt=True, data=data)

    @staticmethod
    def _decrypt(key, iv, data):
        return Crypto._crypt(key=key, iv=iv, encrypt=False, data=data)

    @staticmethod
    def _crypt(key, iv, encrypt, data):
        if not iv:
            iv = b'\x00' * 16
        cipher = Cipher(
            algorithms.AES(key), modes.CBC(iv), backend=Crypto._backend
        )
        if encrypt:
            cryptor = cipher.encryptor()
        else:
            cryptor = cipher.decryptor()

        return cryptor.update(data) + cryptor.finalize()


class Padding(object):
    """
    Padding base class.
    """
    @staticmethod
    def size(length, alignment):
        """
        Calculate needed padding size.

        Args:
            length (int): Data size
            alignment (int): Data alignment

        Returns:
            int: Padding size
        """
        overlap = length % alignment
        if overlap:
            return alignment - overlap
        else:
            return 0

    @staticmethod
    def pad(payload, alignment):
        """
        Abstract method to override

        Args:
            payload (bytes): Data blob
            alignment (int): Data alignment

        Returns:
            bytes: Data with padding bytes
        """
        raise NotImplementedError()

    @staticmethod
    def remove(payload):
        """
        Common method for removing padding from data blob.

        Args:
            payload (bytes): Padded data.

        Returns:
            bytes: Data with padding bytes removed
        """
        pad_count = payload[-1]
        return payload[:-pad_count]


class PKCS7Padding(Padding):
    @staticmethod
    def pad(payload, alignment):
        """
        Add PKCS#7 padding to data blob.

        Args:
            payload (bytes): Data blob
            alignment (int): Data alignment

        Returns:
            bytes: Data with padding bytes
        """
        size = Padding.size(len(payload), alignment)
        if size == 0:
            return payload
        else:
            return payload + (size * chr(size).encode())


class ANSIX923Padding(Padding):
    @staticmethod
    def pad(payload, alignment):
        """
        Add ANSI.X923 padding to data blob.

        Args:
            payload (bytes): Data blob
            alignment (int): Data alignment

        Returns:
            bytes: Data with padding bytes
        """
        size = Padding.size(len(payload), alignment)
        if size == 0:
            return payload
        else:
            return payload + ((size - 1) * b'\x00') + chr(size).encode()
