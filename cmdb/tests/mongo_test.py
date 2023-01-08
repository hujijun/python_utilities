import datetime

import bson

from cmdb.sainc.mongo import MongoService

class UserService:
    table_name = 'user'

    def __init__(self, m):
        self.mongo_service = m
        self.table = self.mongo_service.db[self.table_name]

    def find_by_user_password(self, user_name: str, password: str):
        try:
            return self.table.find({"name": user_name, "password": password}).limit(-1).next()
        except:
            pass


m = MongoService("mongodb://root:example@192.168.87.129:27017")
# m.create_table('aa', [{"field": 'name', 'required': True, 'type': 'string'}])


a = UserService(m).find_by_user_password('aa', "bb")
print(dir(a['_id']))

m.close()
