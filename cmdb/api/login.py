import time

from cmdb.sainc.http import HandlerInterface, ApiException
from cmdb.sainc.utils import new_sha_password, new_token


class Login(HandlerInterface):

    def verify(self):
        # {"username":"admin","password":"abc123"}
        if 'username' not in self.body or 'password' not in self.body:
            raise ApiException(b'500', '用户密码不能为空'.encode())
        username = self.body.get("username")
        password = new_sha_password(self.body.get("password").encode())
        if not(username == 'admin' and password == '970f9470656a0d289dc5c20f331b4cfe37238d05'):
            raise ApiException(b'500', '用户密码错误'.encode())

    def call(self):
        self.verify()
        # token 一小时过期
        user_id = 1
        expire_time = int(time.time()) + 360
        authority = ['admin']
        token = new_token([expire_time, user_id, authority])
        return {
            "name": 'Javsen',
            "avatar": 'https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png',
            "userid": '00000001',
            "signature": '海纳百川，有容乃大',
            "title": '交互专家',
            "group": '蚂蚁金服－某某某事业群－某某平台部－某某技术部－UED',
            "tags": [{"key": '0', "label": '很有想法的'}, {"key": '1', "label": '专注设计'},
                     {"key": '2', "label": '辣~'}],
            "notifyCount": 12,
            "unreadCount": 11,
            "country": 'China',
            "geographic": {"province": {"label": '浙江省', "key": '330000'},
                           "city": {"label": '杭州市', "key": '330100'}},
            "address": '西湖区工专路 77 号',
            "phone": '0752-268888888',
            "authority": authority,
            "expireTime": expire_time,
            "token": token}