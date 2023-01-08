from cmdb.sainc.mongo import MongoTable


class UserService(MongoTable):
    table_name = 'user'

    def find_by_user_password(self, user_name: str, password: str):
        try:
            return self.table.find({
                "username": user_name,
                "password": password
            }).limit(-1).next()
        except:
            pass

    def to_dict(self, item: dict):
        item = super().to_dict(item)
        del item['password']
        return item
