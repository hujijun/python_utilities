from cmdb.sainc.mongo import MongoService

m = MongoService("mongodb://root:example@192.168.87.129:27017")

# m.create_table("user", [
#     {"field": 'name', 'required': True, 'type': 'string', "title": "名称"},
#     {"field": 'username', 'required': True, 'type': 'string', "title": "名称"},
#     {"field": 'password', 'required': True, 'type': 'string', "title": "密码"},
#     {"field": 'isLogin', 'required': True, 'type': 'bool', "title": "可登录"},
#     {"field": 'authority', 'required': False, 'type': 'array', "title": "权限"},
# ])

m.create_table("cmdb_resource_mode", [
    {"field": 'name', 'required': True, 'type': 'string', "title": "名称"},
    {"field": 'tableName', 'required': True, 'type': 'string', "title": "表名"},
    {"field": 'fields', 'required': True, 'type': 'array', "title": "字段"},
])
