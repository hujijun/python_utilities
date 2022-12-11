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

