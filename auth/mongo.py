from sanic.log import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.uri_parser import parse_uri


class MongoCore:

    def __init__(self, app, uri: str):
        self.mongodb = None
        self.uri = uri
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        @app.listener("before_server_start")
        async def init_mongo_connection(app, loop):
            db_params = parse_uri(self.uri)
            self.mongodb = AsyncIOMotorClient(db_params.get('host'), is_loop=loop)[db_params.get("database")]

        @app.listener("before_server_stop")
        async def sub_close(app, loop):
            logger.info(f"mongo connection closed")
            app.mongodb.client.close()
        app.mongodb = self.mongodb
        return self

