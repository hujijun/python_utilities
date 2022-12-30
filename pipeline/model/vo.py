from pipeline.utils import get_timestamp
from task_enum import TaskStatus


class TaskInstance:

    id: int
    start_time: int
    status: TaskStatus
    end_time: int

    def __init__(self):
        self._status = TaskStatus.wait

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if status == TaskStatus.executing:
            """任务开始执行"""
            self.start_time = get_timestamp()
        elif status == TaskStatus.completed:
            """任务执行完成"""
            self.end_time = get_timestamp()
        self._status = status


class VoInterface(object):

    def to_str(self):
        pass


class AtomVo(VoInterface):

    def __init__(self, name: str, func, **kwargs):
        # 步骤名称
        self.atom_name = name
        # 重试次数 默认为0不支持重试
        self.retry_number = kwargs.get("retry_number", 0)
        # 超时次数 默认为0
        self.timeout_number = kwargs.get("timeout_number", 0)
        self.depend_fail_count = kwargs.get("depend_fail_count", 0)
        self.skippable = kwargs.get("skippable", 0)
        self.meta = kwargs.get("meta", 0)
        self.status = kwargs.get("status", 0)
        self.params = kwargs.get("params", {})
        self.func = func

