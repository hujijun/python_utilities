from enum import IntEnum, unique


@unique
class OrderStateEnum(IntEnum):
    """工单状态"""

    # 待审批
    Created = 0
    # 已撤回
    Cancelled = 1
    # 审批中(至少一人开始审批)
    UnderReview = 2
    # 审批通过待执行
    Approved = 3
    # 已驳回
    Rejected = 4
    # 已取消
    Cancel = 5
    # 执行中
    Executing = 6
    # 执行成功
    Successed = 7
    # 执行失败
    ExecuteFailed = 8
    # # 执行异常 可重试
    # ExecuteError = 9
    # 初始化失败
    InitError = 20
    # 任务结束入库失败
    EndError = 30
    # 已关闭
    Closed = 40
    # 暂停
    PAUSE = 15

@unique
class TaskStateEnum(IntEnum):
    """任务状态"""

    # 待执行
    WAIT = 4
    # 执行中
    PROCESS = 3
    # 执行完成
    SUCCESS = 1
    # 执行失败
    ERROR = 2
    # 暂停
    PAUSE = 5

@unique
class StepStateEnum(IntEnum):
    """步骤状态"""

    # 待执行
    WAIT = 4
    # 执行中
    PROCESS = 3
    # 执行完成
    SUCCESS = 1
    # 执行失败
    ERROR = 2
    # 重试中
    RETRYING = 5
    # 执行超时
    TIMEOUT = 6
    # 已跳过
    SKIPPED = 7
    # 暂停
    PAUSE = 8
