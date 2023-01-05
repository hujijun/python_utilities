import logging
import base64
import hashlib
import hmac
import time
import ujson

def new_sha_password(body: bytes) -> str:
    """生成单向不可"""
    sha = hashlib.sha1()
    # 前后加盐
    sha.update(b"abc")
    sha.update(body)
    # 前后加盐
    sha.update(b"abc")
    return sha.hexdigest()


def new_token(body):
    body = base64.b64encode(ujson.dumps(body).encode())
    return new_sign(body) + body.decode()


def new_sign(body: bytes):
    return hmac.HMAC(b'keaaeay', body, hashlib.md5).hexdigest()


def verify_sign(body: bytes, auth: str) -> int:
    if not isinstance(body, bytes) or len(body) < 32:
        logging.info(f"body:{body}")
        return 0
    sign, user = body[:32], body[32:]
    sign2 = new_sign(user).encode()
    logging.info(f"{user}, {sign}, {sign2}")
    if not hmac.compare_digest(sign, sign2):
        logging.info(f"sign error")
        return 0
    user: list = ujson.loads(base64.b64decode(user))
    logging.info(user)
    expire_time = user.pop(0)
    user_id = user.pop(0)
    auths = user.pop(0)
    if expire_time < time.time():
        logging.info(f"expire time")
        # token过期
        return 0
    if auth not in auths:
        logging.info(f"not auth")
        return 0
    return user_id

