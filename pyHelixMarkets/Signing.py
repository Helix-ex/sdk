from secp256k1 import PrivateKey
from hashlib import sha256
import base64
import time

class Signing:

    _huid: str = None
    _public_key: str = None
    _private_key: PrivateKey = None

    def __init__(self, huid: int, private_key: str):
        self._huid = str(huid)
        # decode the api key from base64
        privateKeyBytes = base64.b64decode(private_key)
        self._private_key = PrivateKey(privateKeyBytes, raw=True)
        # generate the corresponding public key
        public_key = self._private_key.pubkey
        # serialize the public key
        serialized_public_key = public_key.serialize(compressed=True)
        # compress to 33 bytes
        pubkey33bytes = serialized_public_key[:33]
        # encode to lowercase hexadecimal string
        self._public_key = pubkey33bytes.hex()

    def _generate_signature(self, ts: int, path: str, method: str, payload: str = None) -> str:
        msg = f"{len(str(ts))}{ts}{len(path)}{path}{len(method)}{method}"
        if payload is not None:
            msg += f"{len(payload)}{payload}"
        # sign message hash with the private key
        signature = self._private_key.ecdsa_sign(msg.encode('utf-8'), digest=sha256)
        # compress to 64 bytes
        signature_compact = self._private_key.ecdsa_serialize_compact(signature)
        # encode to lowercase hexadecimal string
        return signature_compact.hex()
    
    def _get_ts(self) -> int:
        return int(time.time() * 1000)      # return unix timestamp in milliseconds

    def GetAuthHeaders(self, path: str, method: str, payload=None) -> dict[str, str]:
        ts = self._get_ts()
        return {
            'HM-CALLER': self._huid,
            'HM-KEY': self._public_key,
            'HM-TS': str(ts),
            'HM-SIGN': self._generate_signature(ts, path, method, payload)
        }