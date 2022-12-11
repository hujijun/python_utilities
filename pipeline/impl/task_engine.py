from pipeline.impl.event import (
    TaskEventDispatch,
    TaskEventListener1,
    TaskEventListener2)
from pipeline.interface.event import TaskEventListenerInterface
from pipeline.model.task_enum import TaskStatus
from pipeline.model.vo import TaskInstance
from pipeline.utils import get_timestamp


class Pipeline(object):
    """任务编排"""

    def run(self):
        """生成任务执行流"""

    def definition(self):
        """定义任务流"""  


class TaskEngine(object):

    @classmethod
    def run(cls, task_inst):
        pass

    @classmethod
    def initialization(cls, task_inst):
        pass

    def __init__(self, task_inst: TaskInstance, pipeline: Pipeline):
        self.task_inst = task_inst
        self.pipeline = pipeline
        self.event = TaskEventDispatch()
        self.event.add_listener(TaskEventListener1(self))
        self.event.add_listener(TaskEventListener2(self))

    def start(self):
        """任务初始化执行"""
        self.event.dispatch(TaskEventListenerInterface.start)
        self.status_change(TaskStatus.executing)
        self.pipeline.run()

    def status_change(self, status: TaskStatus):
        if status == TaskStatus.executing:
            """任务开始执行"""
            self.task_inst.start_time = get_timestamp()
        elif status == TaskStatus.error:
            """任务执行出错"""
            self.error()
        elif status == TaskStatus.completed:
            """任务执行完成"""
            self.task_inst.end_time = get_timestamp()
            self.completed()
        self.task_inst.status = status

    def completed(self):
        """任务执行完成"""
        self.event.dispatch(TaskEventListenerInterface.completed)

    def error(self):
        """任务执行错误"""
        self.event.dispatch(TaskEventListenerInterface.error)

