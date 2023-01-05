import hashlib
import hmac
import secrets


def encode(payload: bytes, key: bytes):
    import base64
    from jwt import api_jws
    aa = base64.urlsafe_b64encode(b'{"typ": "JWT", "alg": "HS256"}') + b"." + base64.urlsafe_b64encode(payload)
    bb = api_jws.get_algorithm_by_name('HS256').sign(aa, key)
    return aa + b'.' + base64.urlsafe_b64encode(bb)


def aa():
    import json
    import jwt
    from jwt import api_jws
    bb = encode(b'{"some": "payload"}', b'secret')
    print(bb)
    encoded = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
    print(encoded)
    cc = api_jws.decode_complete('eyJ0eXAiOiAiSldUIiwgImFsZyI6ICJIUzI1NiJ9.eyJzb21lIjogInBheWxvYWQifQ.YfN1FdOhi0kEuuaZVzmaAJLz_Z603KhAO3MQyvzRDtw', "secret", algorithms=["HS256"])
    print(cc)

def bb():
    return ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(8))

def cc():
    import secrets
    return secrets.token_hex(16)


def new_sign(body: bytes):
    return hmac.HMAC(b'keaaay', body, hashlib.md5).hexdigest()


def verify_sign(body: str):
    return hmac.compare_digest(body, new_sign(b'aaaas'))



if __name__ == "__main__":
    a = verify_sign('7d14f05b96d0638d7c70c62eba0bf17e')
    print(a)