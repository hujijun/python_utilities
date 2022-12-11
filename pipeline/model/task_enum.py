import enum


class TaskStatus(enum.IntEnum):

    # 待执行
    wait = 1
    # 任务失败退出
    error = 2
    # 执行中
    executing = 3
    # 执行完成退出
    completed = 10
