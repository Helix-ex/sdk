from secp256k1 import PublicKey
import asyncio
import json
import os
import sys

# change the current working directory to the parent directory to load helix_secret.cfg
os.chdir('../')
# add the path to the system path to use the modules
sys.path.append('./')

from Signing import Signing

async def main():
    huid: int = 123456
    api_token: str = 'wgf0xP8mR6BIN0gnHje+y/i8Xfbwgwjcu+/tVySy+0g='
    path = '/funding'
    method = 'GET'
    payload = '{"symbol":"BTC", "kind":"external_to_fund"}'

    signing = Signing(huid, api_token)
    headers = signing.GetAuthHeaders(path, method, payload)
    headers_formatted = json.dumps(headers, indent=2)
    print(headers_formatted)

    # verify the signature
    hm_caller = headers['HM-CALLER']
    hm_key = headers['HM-KEY']
    hm_ts = headers['HM-TS']
    hm_sign = headers['HM-SIGN']

    message = f"{len(hm_ts)}{hm_ts}{len(path)}{path}{len(method)}{method}"
    if payload is not None:
        message += f"{len(payload)}{payload}"

    hm_key_bytes = bytes.fromhex(hm_key)
    pubkey = PublicKey(hm_key_bytes, raw=True)
    signature_bytes = bytes.fromhex(hm_sign)
    signature = pubkey.ecdsa_deserialize_compact(signature_bytes)
    match = pubkey.ecdsa_verify(message.encode('utf-8'), signature)
    print(f"Signature matches: {match}")

if __name__ == "__main__":
    asyncio.run(main())