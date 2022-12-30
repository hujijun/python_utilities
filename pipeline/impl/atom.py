import abc

from pipeline.interface.atom import AtomInterface


class AtomBast(AtomInterface, abc.ABC):
    """原子执行基础实现"""

    def delay_check_status(self, countdown=60):
        """延后检查任务状态，超时告警"""
        task_id = tasks.atom_actuator_factory.apply_async((self.task_inst.id, self.subtask_id, self.step, self.subtask_info.get('lifecycle')), countdown=countdown)
        utils.logger.info(f"发送延后检查任务: {self.tas}:{self.subtask_id}:{self.step}:{self.subtask_info.get('lifecycle')}: {task_id}")

    def execute_atom(self, interval_time=None):
        """执行原子"""
        utils.logger.info(f"{self.log_prefix} 开始执行:{self.atom_info}")
        self.execute()
        if self.is_next:
            self.event.atom_success(self.subtask_id, self.step)
            interval_time = 0
        elif interval_time is None:
            interval_time = self.timeout_task_interval
        self.delay_check_status(interval_time)

    def wait_execute(self):
        """待执行"""
        if self.check_before_depends():
            # 无依赖/依赖步骤成功，执行原子
            if self.is_pause:
                # 暂停
                self.event.atom_pause(self.subtask_id, self.step, self.atom_info)
                self.task_engine.status_change(3)
            else:
                self.event.atom_start(self.subtask_id, self.step, self.atom_info, self.subtask_info)
                self.execute_before()
                self.execute_atom()
        else:
            # 依赖检查失败
            # if self.atom_info.get('depend_fail_count') >= self.depend_count:
            #     # 超过总依赖超时次数，任务退出
            #     raise ExecuteException('超过总依赖超时次数', retry=False, failed_type=task_enum.StepStateEnum.TIMEOUT.value)
            self.event.atom_depend(self.subtask_id, self.step)
            self.delay_check_status(self.timeout_task_interval)

    def executing(self):
        """执行中"""
        utils.logger.info(f"{self.log_prefix} 执行中")
        if self.atom_info.get('timeout_count') + 1 >= self.timeout_count:
            raise execute.ExecuteException('超时次数超限', failed_type=task_enum.StepStateEnum.ERROR.value)
        if storage_block.now_timestamp() > (self.timeout + float(self.atom_info.get('start_time'))):
            # 执行超时；
            self.event.atom_timeout(self.subtask_id, self.step)
        if self.retry_count == -1:
            self.execute_atom(self.retry_task_interval)
            return
        self.delay_check_status(self.timeout_task_interval)

    def execute_error(self, error_msg=None):
        """执行失败"""
        if not error_msg:
            error_msg = self.atom_info.get('error_msg')
        if self.atom_info.get('retry') != 1:
            # 不支持重试，修改状态为失败，退出任务
            raise execute.ExecuteException(error_msg, failed_type=task_enum.StepStateEnum.ERROR.value)
        if self.retry_count == -1:
            # 轮询执行
            utils.logger.info(f"{self.log_prefix} 执行轮询中 {error_msg}")
            self.event.atom_retrying(self.subtask_id, self.step, error_msg)
        else:
            utils.logger.info(f"{self.log_prefix} 执行失败：{error_msg}")
            self.execute_after_error()
            # 失败重试
            self.event.atom_error_retrying(self.subtask_id, self.step, error_msg)
        self.delay_check_status(self.retry_task_interval)

    def execute_retry(self):
        """失败重试"""
        utils.logger.info(f"{self.log_prefix} 重试中")
        try:
            start_time = float(self.atom_info.get('start_time'))
        except:
            raise execute.ExecuteException("执行超时", failed_type=task_enum.StepStateEnum.ERROR.value)
        if storage_block.now_timestamp() > (self.timeout + start_time):
            msg = "执行超时"
            if self.retry_count == -1 and self.atom_info.get('error_msg'):
                msg = self.atom_info.get('error_msg')
            raise execute.ExecuteException(msg, failed_type=task_enum.StepStateEnum.ERROR.value)
        if self.retry_count != -1 and self.atom_info.get('retry_count') > self.retry_count:
            # 超过总重试次数，修改状态为失败，退出任务
            raise execute.ExecuteException(f"执行{self.atom_info.get('retry_count')}次未成功",
                                           failed_type=task_enum.StepStateEnum.ERROR.value)
        self.execute_atom(self.retry_task_interval)

    def execute_success(self):
        """执行成功"""
        if self.subtask_info.get('status') == task_enum.TaskStateEnum.SUCCESS.value:
            utils.logger.info(f"{self.log_prefix} 当前子任务执行成功，丢掉")
            return
        if self.atom_info.get('status') == task_enum.StepStateEnum.SKIPPED.value:
            utils.logger.info(f"{self.log_prefix} 执行跳过")
        elif self.atom_info.get('status') == task_enum.StepStateEnum.SUCCESS.value:
            utils.logger.info(f"{self.log_prefix} 执行成功")
        if self.subtask_info.get('status') == task_enum.TaskStateEnum.ERROR.value:
            # 更新工单，任务状态为执行中
            self.event.subtask_executing(self.subtask_id)
        self.execute_after_success(self.atom_info.get('status'))
        # 有通知被依赖的原子
        self.notice_after_depends()
        if self.subtask_info.get('total_steps') == self.step:
            # 子任务执行完成, 检查主任务状态
            self.event.subtask_success(self.subtask_id, self.step)
            self.task_engine.status_change(1)
        else:
            # 执行下一步
            self.event.atom_next(self.subtask_id, self.step)
            task_id = tasks.atom_actuator_factory.apply_async(
                (self.task_inst.id, self.subtask_id, self.step + 1, self.subtask_info.get('lifecycle')))
            utils.logger.info(f"{self.log_prefix}执行成功，激活下一步任务: {task_id}")

    def run(self):
        if self.atom_info.get('status') == task_enum.StepStateEnum.PAUSE.value:
            # 暂停
            utils.logger.info(f"{self.log_prefix} 步骤暂停")
            return
        if self.atom_info.get("pause_user"):
            # 人工中止
            utils.logger.info(f"{self.log_prefix} 人工中止")
            self.event.subtask_failed(self.subtask_id, self.step, f'已被{self.atom_info.get("pause_user")}中止')
            self.task_engine.status_change(2)
            return
        execute_mapping = {
            # 执行成功
            task_enum.StepStateEnum.SUCCESS.value: self.execute_success,
            # 跳过
            task_enum.StepStateEnum.SKIPPED.value: self.execute_success,
            # 执行失败
            task_enum.StepStateEnum.ERROR.value: self.execute_error,
            # 自动重试
            task_enum.StepStateEnum.RETRYING.value: self.execute_retry,
            # 待执行
            task_enum.StepStateEnum.WAIT.value: self.wait_execute,
            # 执行中
            task_enum.StepStateEnum.PROCESS.value: self.executing}
        try:
            if self.atom_info.get('status') not in execute_mapping:
                raise execute.ExecuteException('错误的步骤状态', failed_type=task_enum.StepStateEnum.ERROR.value)
            execute_mapping[self.atom_info.get('status')]()
        except execute.ExecuteException as error:
            if error.is_retry:
                self.execute_error(error.msg)
            else:
                # 失败退出
                utils.logger.info(f"{self.log_prefix} 执行失败退出 {error.msg}")
                self.event.subtask_failed(self.subtask_id, self.step, error.msg, meta=error.meta)
                self.task_engine.status_change(2)
        except Exception as error:
            utils.logger.exception(f"{self.log_prefix} 执行异常: {error}")
            self.event.atom_error_retrying(self.subtask_id, self.step, '执行异常')
            self.delay_check_status(self.timeout_task_interval)
