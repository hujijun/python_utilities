"""
任务执行实现
"""
import abc
import json

from pipeline.impl import decorators
from pipeline.task_enum import TaskStateEnum, OrderStateEnum
from pipeline.execute import TaskException
from pipeline.interface.task_engine import TaskEngineInterface


def check_task(task_id):
    """检查任务"""
    task_inst = TaskInstance.query.filter(TaskInstance.id == task_id).first()
    if not task_inst:
        raise TaskException(f"未找到任务数据,TaskId:{task_id}", failed_type=task_enum.StepStateEnum.ERROR.value)
    return task_inst


def task_event(func):
    def wrapper(self, *args, **kwargs):
        print(func)
        print(type(func))
        if isinstance(self, TaskEngine):
            pass
        print(self, *args, **kwargs)
        func(self, *args, **kwargs)
    return wrapper


class TaskEngine(TaskEngineInterface, abc.ABC):

    @task_event
    def init_and_start(self):
        """任务初始化"""
        try:
            self.init_before()  # 初始化前
            # 获取定义的原子编排
            subtask_info_list = self.get_definition_atomic_choreography()
            self.block.init_set_task_info(subtask_info_list)  # 写 redis
            self.init_after()  # 初始化后
            # 激活任务 执行第一步
            atom_actuator_factory.apply_async((self.task_inst.id, subtask_info.get('id'), 1, 0))
        except Exception as error:
            error_content = '任务初始化失败'
            if isinstance(error, TaskException):
                error_content += f', {error.msg}'
            utils.logger.exception(f"{self.task_name}[{self.task_inst.id}]: {error_content}")
            try:
                self.event.task_error(task_enum.OrderStateEnum.InitError.value, error_content)
            except:
                pass
            self.init_error()  # 初始化失败

    @decorators.order_lock
    def status_change(self, _type: int):
        """工单状态变更
        t 1 子任务完成， 2 子任务失败, 3 子任务暂停
        """
        task_info = self.block.get_task_info()
        if not task_info:
            utils.logger.info(f"{self.task_name}[{self.task_inst.id}] 工单数据不存在，可能已执行成功，不执行状态变更")
            return
        status = set()
        for subtask_id in task_info:
            subtask_info = json.loads(task_info[subtask_id])
            if subtask_info['status'] in (task_enum.TaskStateEnum.PROCESS.value, task_enum.TaskStateEnum.WAIT.value):
                # 遍历所有任务状态, 有 待执行 或 执行中 则退出当前子任务锁
                return
            status.add(subtask_info['status'])
        # 剩余的任务状态只有 成功 暂停 失败 三种
        if _type == 1:
            if TaskStateEnum.ERROR.value in status:
                # 当前子任务成功, 存在子任务失败, 则主任务为失败
                self.event.task_error(OrderStateEnum.ExecuteFailed.value)
                return
            if TaskStateEnum.PAUSE.value in status:
                # 存在子任务暂停
                self.event.task_pause()
                return
            if len(status) == 1 and TaskStateEnum.SUCCESS.value == status.pop():
                # 当前子任务成功, 且状态列表只有成功状态, 则主任务为成功
                try:
                    # 所有子任务执行成功入库
                    self.end_before()
                    self.event.task_success()
                    # 清除任务数据
                    task_info = self.block.clear_task_info()
                    self.block.clear_data_sync_seq(task_info)
                except Exception as error:
                    utils.logger.exception(error)
                    self.event.task_error(OrderStateEnum.EndError.value, f"任务入库清理执行失败")
        elif _type == 2:
            # 当前子任务失败, 由于没有待执行/执行中子任务, 主任务直接失败
            self.event.task_error(OrderStateEnum.ExecuteFailed.value)
        elif _type == 3:
            # 当前子任务暂停, 但状态列表有失败任务, 则主任务为失败
            if TaskStateEnum.ERROR.value in status:
                self.event.task_error(OrderStateEnum.ExecuteFailed.value)
                return

    def end_before(self):
        """执行结束"""
        db.session.add(TaskExecuteStatus(meta=live_data.live_data(self.task_inst, self.block), task_id=self.task_inst.id))
        db.session.commit()