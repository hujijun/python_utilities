from typing import Tuple
import pyotp


class OtpService(object):
    """二次认证基础封装"""

    @staticmethod
    def new_secret() -> str:
        """生成64位密钥"""
        return pyotp.random_base32(64)

    @classmethod
    def get_secret(cls, username: str) -> Tuple[str, str]:
        """
        """
        secret_key: str = cls.new_secret()
        # 将密钥和用户名转换为totp格式给前端生成二唯码:
        # otpauth://totp/admin?secret=EISOKPDCZYSXNQKK7UQUWM7OR6GAMJUSHA3CVU5YQKVAREYIKV6X2OKP7K32ZZ7K
        return secret_key, pyotp.totp.TOTP(secret_key).provisioning_uri(username)

    @staticmethod
    def verify_code(secret_key: str, verify_code: int):
        """验证"""
        return pyotp.TOTP(secret_key).verify(verify_code)
