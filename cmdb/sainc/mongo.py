import pymongo
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

    def create_table(self, table_name: str, validator, validationLevel='strict', validationAction='error'):
        validator = {
            "$jsonSchema": {
                "properties": {
                    "name": {"bsonType": "string"},
                    "label": {"bsonType": "string"}
                },
                "required": ["name"]
            }
        }
        self.db.create_collection(
            table_name,
            validator=validator,
            validationLevel=validationLevel,
            validationAction=validationAction)

    def del_table(self, table_name: str):
        self.db.drop_collection(table_name)


class MongoTable(object):

    def __init__(self, mongo_service: MongoService, table_name: str):
        self.mongo_service = mongo_service
        self.table = self.mongo_service.db[table_name]

    def insert_one(self, body: dict):
        self.table.insert_one(body)

    async def insert_many(self, body: list):
        self.table.insert_many(body)

    def find(self):
        return self.table.find()

