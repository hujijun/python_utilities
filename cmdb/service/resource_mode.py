from cmdb.sainc.mongo import MongoTable, MongoService


class BaseService(object):
    _table_name: str

    def __init__(self):
        self.mode = MongoTable(MongoService.instance, self._table_name)


class ResourceModeService(BaseService):
    _table_name = "cmdb_resource_mode"

    def page(self):
        data = self.mode.table.find()
        for i in data:
            self.to_dict(i)
        count = self.mode.table.count_documents({})
        return {"count": count, 'data': []}

    def to_dict(self, inst):
        print(inst)

