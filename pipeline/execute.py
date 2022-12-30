from pipeline.task_enum import StepStateEnum, TaskStateEnum


class AtomException(Exception):
    """原子异常"""
    def __init__(self, msg: str, failed_type=StepStateEnum.RETRYING):
        Exception.__init__(self)
        self.msg = msg
        self.is_retry = True if failed_type == StepStateEnum.RETRYING else False
        self.failed_type = failed_type


class TaskException(Exception):
    """任务异常"""
    def __init__(self, msg: str, failed_type=TaskStateEnum.RETRYING):
        Exception.__init__(self)
        self.msg = msg
        self.is_retry = True if failed_type == StepStateEnum.RETRYING else False
        self.failed_type = failed_type
