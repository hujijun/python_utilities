import logging

from cmdb.sainc.mongo import MongoService
from cmdb.sainc.http import HttpService
from api import login
from api.mode import modelist


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(filename)s:%(levelname)s: %(message)s")
    router = {
        b'/login': login.Login,
        b'/modeList': modelist.ModelList,
    }
    MongoService.instance = MongoService("mongodb://root:example@192.168.87.129:27017")
    HttpService(router).run()
