import pymongo
from bson import ObjectId
from pymongo.collection import Collection, Cursor
from pymongo.uri_parser import parse_uri


class MongoService(object):
    instance = None

    def __init__(self, uri: str):
        self.db_name = 'dev'
        # self.db_name = parse_uri(uri).get("database")
        self.uri = uri
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = pymongo.MongoClient(self.uri)
            s = self._client.start_session()
        return self._client

    @property
    def db(self):
        return self.client[self.db_name]

    def close(self):
        if self._client:
            self._client.close()

    def create_table(self, table_name: str, fields: list, validationLevel='strict', validationAction='error'):
        validator = {"$jsonSchema": {"properties": {}, "required": []}}
        for i in fields:
            validator['$jsonSchema']['properties'][i['field']] = {"bsonType": i['type'], "title": i['title']}
            if i['required']:
                validator['$jsonSchema']['required'].append(i['field'])
        self.db.create_collection(
            table_name,
            validator=validator,
            validationLevel=validationLevel,
            validationAction=validationAction)

    def update_table(self, table_name: str, fields: list):
        validator = {"$jsonSchema": {"properties": {}, "required": []}}
        for i in fields:
            validator['$jsonSchema']['properties'][i['field']] = {"bsonType": i['type'], "title": i['title']}
            if i['required']:
                validator['$jsonSchema']['required'].append(i['field'])
        self.db.command({"collMod": table_name, "validator": validator})

    def del_table(self, table_name: str):
        self.db.drop_collection(table_name)


class MongoTable(object):
    table_name: str

    def __init__(self):
        self.mongo_service: MongoService = MongoService.instance
        self.table: Collection = self.mongo_service.db[self.table_name]

    def insert_one(self, body: dict):
        self.table.insert_one(body)

    def edit_one(self, filter: dict, update: dict):
        return self.table.update_one(filter, update)

    def edit_by_id(self, _id: ObjectId, update: dict):
        if isinstance(_id, str):
            _id = ObjectId(_id)
        return self.table.update_one({"_id": _id}, {"$set": update})

    async def insert_many(self, body: list):
        self.table.insert_many(body)

    def find(self):
        return self.table.find()

    def find_by_id(self, _id: ObjectId) -> dict:
        if isinstance(_id, str):
            _id = ObjectId(_id)
        try:
            return self.table.find({"_id": _id}).limit(-1).next()
        except:
            pass

    def get_create_time(self, _id):
        return _id.generation_time.timetuple()

    def page(self, filters: dict, params: dict):
        current: int = params.get("current", 1)
        page_size: int = params.get("pageSize", 15)
        if params.get('_id'):
            filters['_id'] = ObjectId(params.get('_id'))
        data = []
        count = self.table.count_documents(filters)
        skip = (current * page_size) - page_size
        if count >= skip:
            for i in self.table.find(filters).limit(page_size).skip(skip):
                data.append(self.to_dict(i))
        return {"total": count, 'data': data, "success": True}

    def to_dict(self, item: dict) -> dict:
        item["createBy"] = item["_id"].generation_time.strftime('%Y-%m-%d %H:%M:%S')
        item["_id"] = str(item["_id"])
        # i["createBy"] = int(i["_id"].generation_time.timestamp())
        return item
