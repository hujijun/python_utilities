import abc


class TaskEventHandlingInterface(object):
    """任务事件处理"""

    @abc.abstractmethod
    def init_and_start(self):
        """任务初始化事件"""

    @abc.abstractmethod
    def fail(self, status: int, msg: str = None):
        """任务失败"""


class AtomEventHandlingInterface(object):
    """原子事件处理"""
