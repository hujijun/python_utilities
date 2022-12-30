import abc


class TaskEngineInterface(object):
    task_name: str
    biz_model = None

    def __init__(self, task_inst):
        self.task_inst = task_inst
        self._biz_inst = None

    @abc.abstractmethod
    def init_before(self):
        """任务初始化前"""

    @abc.abstractmethod
    def init_after(self):
        """任务初始化后"""

    def init_error(self):
        """任务初始化失败"""

    @abc.abstractmethod
    def end_before(self):
        """执行结束前触发"""

    @property
    def biz_inst(self):
        if not self._biz_inst:
            self._biz_inst = self.biz_model.query.filter_by(id=self.task_inst.business_id).first()
        return self._biz_inst
