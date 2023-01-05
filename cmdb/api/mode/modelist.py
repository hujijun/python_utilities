from cmdb.sainc.http import HandlerInterface
from cmdb.service.resource_mode import ResourceModeService


class ModelList(HandlerInterface):
    auth = 'admin'

    def call(self):
        return ResourceModeService().page()
