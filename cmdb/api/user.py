import time

from cmdb.sainc import utils
from cmdb.sainc.http import HandlerInterface, ApiException
from cmdb.sainc.utils import new_sha_password, new_token
from cmdb.service.user import UserService


class Login(HandlerInterface):

    def verify(self):
        if 'username' not in self.body or 'password' not in self.body:
            raise ApiException(b'500', '用户密码不能为空'.encode())
        username = self.body.get("username")
        password = new_sha_password(self.body.get("password").encode())
        # user = {"_id": 1, "authority": ["admin"]}
        user = UserService().find_by_user_password(username, password)
        if not user:
            raise ApiException(b'500', '用户密码错误'.encode())
        if not user['isLogin']:
            raise ApiException(b'500', '限制登录请与联系管理员'.encode())
        return user

    def call(self):
        user = self.verify()
        user_id = str(user["_id"])
        authority = user['authority']
        expire_time = int(time.time()) + 3600
        token = new_token([expire_time, user_id, authority])
        return {
            "name": user['name'],
            "avatar": 'https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png',
            "userid": user_id,
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


class Register(HandlerInterface):
    auth = 'admin'

    def verify(self):
        if 'username' not in self.body or 'password' not in self.body:
            raise ApiException(b'500', '用户密码不能为空'.encode())

    def call(self):
        self.verify()
        # 通过单向加密生成入库密码， 登陆校验密码使用同样方式生成的密码是否一致
        password = utils.new_sha_password(self.body['password'].encode())
        body = {
            "name": self.body['name'],
            "username": self.body['username'],
            "authority": self.body['authority'],
            "isLogin": True,
            "password": password}
        UserService().insert_one(body)
        return {"status": 'success'}


class UserList(HandlerInterface):
    auth = "admin"

    def call(self):
        filters = {}
        if self.body.get("username"):
            filters['username'] = self.body.get("username")
        return UserService().page(filters, self.body)
