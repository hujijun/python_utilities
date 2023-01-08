from bson import ObjectId
from cmdb.sainc.http import HandlerInterface, ApiException
from cmdb.service.resource_mode import ResourceModeService


class ModelList(HandlerInterface):
    auth = 'admin'

    def call(self):
        return ResourceModeService().page({}, self.body)


class AddMode(HandlerInterface):
    auth = 'admin'

    def call(self):
        service = ResourceModeService()
        service.mongo_service.create_table(self.body['tableName'], self.body['fields'])
        service.insert_one(self.body)
        return {"status": "success"}


class EditMode(HandlerInterface):
    auth = 'admin'

    def call(self):
        _id = ObjectId(self.body["id"])
        del self.body['id']
        service = ResourceModeService()
        inst = service.find_by_id(_id)
        if not inst:
            raise ApiException(b'500', '未找到'.encode())
        service.edit_by_id(_id, {"name": self.body['name'], "fields": self.body['fields']})
        service.mongo_service.update_table(inst['tableName'], self.body['fields'])
        return {"status": "success"}
