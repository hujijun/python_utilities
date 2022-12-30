import datetime
import json
import time
import uuid
import settings
from zlib import compress
from celery_tasks import tasks, utils
from celery_tasks.factory import task_enum, block as storage_block, live_data
from common import exception
from common.utils import get_now_utc, datetime_to_string
from pipeline.impl.model import OpenPlan, db, TaskExecuteLog
from service.task import task_execute_log, task_notifier
from service.middleware import rabbit_service


def get_task_status_name(status, is_step=True) -> str:
    """获取任务状态中文名"""
    context = {1: '执行成功', 2: '执行失败', 3: '执行中', 4: '待执行'}
    if is_step:
        context.update({5: '重试中', 6: '执行超时', 7: '已跳过', 8: '暂停'})
    else:
        context.update({5: '暂停'})
    return context.get(status, status)


class EventHandling(object):
    """事件处理，状态变更通知"""

    def __init__(self, block: storage_block.Block):
        self.block = block
        self.task_engine = None
        self.task_id = self.block.task_inst.id

    @staticmethod
    def send_mq(task_id, **kwargs):
        data = {'id': int(task_id)}
        try:
            if kwargs.get('status') is not None:
                data['status'] = kwargs.get('status')
            if isinstance(kwargs.get('jobs'), dict):
                data['jobs'] = [kwargs.get('jobs')]
            elif isinstance(kwargs.get('jobs'), list):
                data['jobs'] = kwargs.get('jobs')
            if kwargs.get('steps'):
                data['steps'] = kwargs.get('steps')
            if kwargs.get('records'):
                data['records'] = kwargs.get('records')
            if kwargs.get('error_msg'):
                t_inst = task_execute_log.task_execute_log_service.add(
                    task_id,
                    kwargs.get('error_msg'),
                    world_id=kwargs.get('subtask_id'),
                    meta=kwargs.get('meta'))
                data['executeLogs'] = [{
                    'id': t_inst.id,
                    'meta': kwargs.get('meta'),
                    'time': datetime_to_string(t_inst.create_time),
                    'content': kwargs.get('error_msg'),
                    'worldId': kwargs.get('subtask_id')
                }]
            if kwargs.get('executeLogs'):
                data['executeLogs'] = kwargs.get('executeLogs')
            if kwargs.get('basicInfo'):
                data['basicInfo'] = kwargs.get('basicInfo')
            if kwargs.get('approvalInfo'):
                data['approvalInfo'] = kwargs.get('approvalInfo')
            body = compress(json.dumps(data).encode())
            if settings.USE_RABBIT_MQ_POOL:
                rabbit_service.RabbitPyPoolService().send_task_status_proxy(body, kwargs.get("isRabbitPy", False))
            else:
                rabbit_service.RabbitPyService.send_task_status_proxy(body)
        except Exception as error:
            utils.logger.exception("发送给前端信息队列异常")

    def task_init_and_start(self, is_send_jobs=True):
        """任务开始执行"""
        self.block.task_inst.status = task_enum.OrderStateEnum.Executing.value
        self.block.task_inst.start_time = get_now_utc()
        db.session.commit()
        steps = {
            'current': 2,
            'status': 'process',
            'step': [{'id': 3, 'time': datetime_to_string(self.block.task_inst.start_time), 'user': '系统'}]
        }
        if not is_send_jobs:
            self.send_mq(self.task_id, status=self.block.task_inst.status, steps=steps)
            return
        try:
            jobs = live_data.live_data(self.block.task_inst, self.block)
            self.send_mq(self.task_id, status=self.block.task_inst.status, steps=steps, jobs=jobs)
        except:
            pass

    def task_error(self, status: int, msg: str = None):
        """任务 初始化/结束异常"""
        self.block.task_inst.status = status
        db.session.commit()
        if self.block.task_inst.type == 10:
            # 开服任务更新开服计划状态
            OpenPlan.query.filter(OpenPlan.task_id == self.block.task_inst.id).update({"status": 8})
            db.session.commit()
        self.send_mq(self.task_id, status=status, error_msg=msg, steps={'current': 2, 'status': 'error'})
        task_notifier.execution_error(self.block.task_inst)
        if msg:
            utils.send_ding_alarm(msg, self.block.task_inst, level=3)

    def task_success(self):
        """任务执行成功"""
        self.block.task_inst.status = task_enum.OrderStateEnum.Successed.value
        self.block.task_inst.end_time = get_now_utc()
        db.session.commit()
        task_notifier.execution_success(self.block.task_inst)
        steps = {'current': 3, 'status': 'finish',
                 'step': [{'id': 4, 'time': datetime_to_string(self.block.task_inst.end_time), 'user': '系统'}]}
        self.send_mq(self.task_id, status=task_enum.OrderStateEnum.Successed.value, steps=steps)

    def task_pause(self):
        """任务暂停"""
        self.block.task_inst.status = task_enum.OrderStateEnum.PAUSE.value
        db.session.commit()
        task_notifier.send_pause(self.block.task_inst)
        steps = {'current': 2, 'status': 'warning', "step": [{"id": 3, "title": "暂停"}]}
        self.send_mq(self.task_id, status=task_enum.OrderStateEnum.PAUSE.value, steps=steps)

    def subtask_success(self, subtask_id: str, step: int):
        """子任务执行成功"""
        atom_info = self.atom_success(subtask_id, step)
        subtask_info = self.block.get_subtask_info(subtask_id)
        subtask_info.update(status=task_enum.TaskStateEnum.SUCCESS.value, end_time=atom_info['end_time'])
        self.block.update_subtask_info(subtask_id, subtask_info)
        jobs = {'id': int(subtask_id), 'status': subtask_info['status'], 'endTime': atom_info['end_time']}
        self.send_mq(self.task_id, jobs=jobs)

    def subtask_failed(self, subtask_id: str, step: int, msg, meta=None):
        """子任务执行失败"""
        subtask_info = self.block.get_subtask_info(subtask_id)
        subtask_info['status'] = task_enum.TaskStateEnum.ERROR.value
        self.block.update_subtask_info(subtask_id, subtask_info)
        atom_info = self.block.get_atom_info(subtask_id, step)
        atom_info['status'] = task_enum.StepStateEnum.ERROR.value
        if 'error_msg' in atom_info:
            del atom_info['error_msg']
        jobs = {'id': int(subtask_id), 'status': subtask_info['status'],
                'steps': [{'id': step, 'status': atom_info['status']}]}
        if isinstance(atom_info.get('meta'), list) and len(atom_info.get('meta')) > 0:
            jobs['steps'][0]['meta'] = []
            for i in atom_info.get('meta'):
                if i.get('status') in [task_enum.StepStateEnum.PROCESS.value, task_enum.StepStateEnum.RETRYING.value]:
                    i['status'] = task_enum.StepStateEnum.ERROR.value
                jobs['steps'][0]['meta'].append({'id': i.get('id'), "statusKey": i.get("statusKey"), 'status': i['status']})
        self.block.update_atom_info(subtask_id, step, atom_info)
        # self.set_depends_error(atom_info.get('after_depends'))
        error_msg = f"{atom_info.get('atom_name')}: {msg}，任务退出"
        self.send_mq(self.task_id, error_msg=error_msg, jobs=jobs, subtask_id=subtask_id, meta=meta)
        utils.send_ding_alarm(error_msg, self.block.task_inst, level=3, world_list=[subtask_id])
        # task_notifier.execution_error(self.block.task_inst)

    def subtask_executing(self, subtask_id: str):
        """子任务状态执行中"""
        if self.block.task_inst.status != task_enum.OrderStateEnum.Executing.value:
            self.block.task_inst.status = task_enum.OrderStateEnum.Executing.value
            db.session.commit()
        subtask_info = self.block.get_subtask_info(subtask_id)
        subtask_info['status'] = task_enum.TaskStateEnum.PROCESS.value
        self.block.update_subtask_info(subtask_id, subtask_info)
        steps = {'status': 'process', "step": [{"id": 3, "title": "执行"}]}
        jobs = {'id': int(subtask_id), 'status': subtask_info['status']}
        self.send_mq(self.task_id, status=self.block.task_inst.status, steps=steps, jobs=jobs)

    def atom_pause(self, subtask_id, step: int, atom_info):
        atom_info['status'] = task_enum.StepStateEnum.PAUSE.value
        atom_info['start_time'] = storage_block.now_timestamp()
        self.block.update_atom_info(subtask_id, step, atom_info)
        subtask_info = self.block.get_subtask_info(subtask_id)
        subtask_info['status'] = task_enum.TaskStateEnum.PAUSE.value
        self.block.update_subtask_info(subtask_id, subtask_info)
        jobs = {
            'id': int(subtask_id),
            'status': subtask_info['status'],
            'steps': [{'id': int(step), "startTime": atom_info['start_time'], 'status': atom_info['status']}]}
        self.send_mq(self.task_id, jobs=jobs)

    def atom_start(self, subtask_id, step: int, atom_info: dict, subtask_info: dict):
        """原子开始执行"""
        atom_info.update(
            status=task_enum.StepStateEnum.PROCESS.value,
            start_time=storage_block.now_timestamp(),
            retry_count=0,
            timeout_count=0,
            depend_fail_count=0)
        if 'exec_params' in atom_info:
            del atom_info['exec_params']
        if 'error_msg' in atom_info:
            del atom_info['error_msg']
        jobs = {
            'id': int(subtask_id),
            'status': atom_info['status'],
            'steps': [{'id': int(step), "startTime": atom_info['start_time'], 'status': atom_info['status']}]}
        if isinstance(atom_info.get('meta'), list) and len(atom_info.get('meta')) > 0:
            jobs['steps'][0]['meta'] = []
            for i in atom_info.get('meta'):
                jobs['steps'][0]['meta'].append({'id': i.get('id'), "statusKey": i.get("statusKey"), 'status': atom_info['status']})
                i['status'] = atom_info['status']
        self.block.update_atom_info(subtask_id, step, atom_info)
        if step == 1:
            subtask_info.update(start_time=atom_info['start_time'], status=atom_info['status'])
            jobs['startTime'] = atom_info['start_time']
            self.block.update_subtask_info(subtask_id, subtask_info)
        if self.block.task_inst.status != task_enum.OrderStateEnum.Executing.value:
            self.block.task_inst.status = task_enum.OrderStateEnum.Executing.value
            db.session.commit()
            self.send_mq(
                self.task_id,
                status=task_enum.OrderStateEnum.Executing.value,
                steps={'current': 2, 'status': 'process', "step": [{"id": 3, "title": "执行"}]}, jobs=jobs)
        else:
            self.send_mq(self.task_id, jobs=jobs)

    def atom_next(self, subtask_id: str, step: int):
        """执行下一步更新数据，通知"""
        self.atom_success(subtask_id, step)
        subtask_info = self.block.get_subtask_info(subtask_id)
        subtask_info['status'] = task_enum.TaskStateEnum.PROCESS.value
        subtask_info['current_step'] += 1
        self.block.update_subtask_info(subtask_id, subtask_info)
        jobs = {
            'id': int(subtask_id),
            'status': subtask_info['status'],
            'currentStep': subtask_info.get('current_step')
        }
        self.send_mq(self.task_id, jobs=jobs)

    def atom_error_retrying(self, subtask_id: str, step: int, msg):
        """原子执行出错重试告警"""
        atom_info = self.block.get_atom_info(subtask_id, step)
        atom_info['status'] = task_enum.StepStateEnum.RETRYING.value
        if atom_info.get('error_msg'):
            del atom_info['error_msg']
        if atom_info['retry_count'] > 0:
            error_msg = f"{atom_info.get('atom_name')}: {msg}, 第{atom_info['retry_count']}次重试"
        else:
            error_msg = f"{atom_info.get('atom_name')}: {msg}"
        atom_info['retry_count'] += 1
        jobs = {
            "id": int(subtask_id),
            'steps': [{'id': int(step), "status": atom_info['status']}]
        }
        if isinstance(atom_info.get('meta'), list) and len(atom_info.get('meta')) > 0:
            jobs['steps'][0]['meta'] = []
            for i in atom_info.get('meta'):
                if i["status"] not in [task_enum.StepStateEnum.SUCCESS.value]:
                    i['status'] = atom_info['status']
                    jobs['steps'][0]['meta'].append({'id': i.get('id'), "statusKey": i.get("statusKey"), 'status': i.get('status')})
        self.block.update_atom_info(subtask_id, step, atom_info)
        utils.send_ding_alarm(error_msg, self.block.task_inst, level=2, world_list=[subtask_id])
        self.send_mq(self.task_id, error_msg=error_msg, subtask_id=subtask_id, jobs=jobs)

    def atom_retrying(self, subtask_id: str, step: int, error_msg: str = None):
        """原子检查状态"""
        atom_info = self.block.get_atom_info(subtask_id, step)
        atom_info['status'] = task_enum.StepStateEnum.RETRYING.value
        if error_msg:
            atom_info['error_msg'] = error_msg
        jobs = {
            "id": int(subtask_id),
            'steps': [{'id': int(step), "status": atom_info['status']}]
        }
        if isinstance(atom_info.get('meta'), list) and len(atom_info.get('meta')) > 0:
            jobs['steps'][0]['meta'] = []
            for i in atom_info.get('meta'):
                if i["status"] not in [task_enum.StepStateEnum.SUCCESS.value]:
                    i['status'] = atom_info['status']
                    jobs['steps'][0]['meta'].append({'id': i.get('id'), "statusKey": i.get("statusKey"), 'status': i.get('status')})
        self.block.update_atom_info(subtask_id, step, atom_info)
        self.send_mq(self.task_id, jobs=jobs)

    def atom_success(self, subtask_id: str, step: int):
        atom_info = self.block.get_atom_info(subtask_id, step)
        if 'error_msg' in atom_info:
            del atom_info['error_msg']
        if atom_info.get('end_time') is None:
            atom_info['end_time'] = storage_block.now_timestamp()
        if atom_info.get('status') != task_enum.StepStateEnum.SKIPPED.value:
            atom_info['status'] = task_enum.StepStateEnum.SUCCESS.value
        self.block.update_atom_info(subtask_id, step, atom_info)
        jobs = {
            'id': int(subtask_id),
            'steps': [{'id': int(step), 'status': atom_info['status'], 'endTime': atom_info['end_time']}]
        }
        if isinstance(atom_info.get('meta'), list) and len(atom_info.get('meta')) > 0:
            jobs['steps'][0]['meta'] = []
            for i in atom_info.get('meta'):
                jobs['steps'][0]['meta'].append({'id': i.get('id'), "statusKey": i.get("statusKey"), 'status': i.get('status')})
        self.send_mq(self.task_id, jobs=jobs)
        return atom_info

    def atom_timeout(self, subtask_id: str, step: int):
        """原子执行超时告警"""
        atom_info = self.block.get_atom_info(subtask_id, step)
        atom_info['timeout_count'] += 1
        self.block.update_atom_info(subtask_id, step, atom_info)
        utils.send_ding_alarm(f"{atom_info.get('atom_name')}: 执行超时", self.block.task_inst, level=2, world_list=[subtask_id])
        self.send_mq(self.task_id, error_msg=f"{atom_info.get('atom_name')}: 执行超时", subtask_id=subtask_id)

    def retry_start(self, subtask_id, step, user=None, is_run=False):
        """单个区服重新执行功能，允许运维管理人员在任务失败后对已经成功的步骤重新执行"""
        subtask_info = self.block.get_subtask_info(subtask_id)
        if subtask_info.get('current_step') < step:
            raise exception.ApiException(1001, f"无法进行该操作!")
        atom_info = self.block.get_atom_info(subtask_id, step)
        if atom_info.get('status') != task_enum.StepStateEnum.SUCCESS.value:
            raise exception.ApiException(1001, f"无法进行该操作!")
        steps = []
        for i in range(step, subtask_info['current_step'] + 1):
            steps.append({"startTime": None, "endTime": None, 'status': task_enum.StepStateEnum.WAIT.value, 'id': i})
            self.block.edit_atom_info(subtask_id, i, {
                "start_time": None,
                "end_time": None,
                "error_msg": None,
                'status': task_enum.StepStateEnum.WAIT.value,
                "pause_user": None})
        subtask_info['status'] = task_enum.TaskStateEnum.PROCESS.value
        subtask_info['current_step'] = step
        self.block.update_subtask_info(subtask_id, subtask_info)
        if self.block.task_inst.status != task_enum.OrderStateEnum.Executing.value:
            self.block.task_inst.status = task_enum.OrderStateEnum.Executing.value
            if self.block.task_inst.type == 10:
                OpenPlan.query.filter(OpenPlan.task_id == self.block.task_inst.id).update({"status": self.block.task_inst.status})
            db.session.commit()
        if user:
            self.send_mq(
                self.task_id,
                subtask_id=subtask_id,
                error_msg=f"{user} 跳至 {atom_info.get('atom_name')} 重试",
                status=self.block.task_inst.status,
                steps={'status': 'process'},
                jobs={'id': int(subtask_id), 'steps': steps, "currentStep": step, 'status': subtask_info['status']})
        if not is_run:
            return
        tasks.atom_actuator_factory.apply_async((self.block.task_inst.id, subtask_id, subtask_info.get('current_step'), subtask_info.get('lifecycle')))

    def manual_retry(self, subtask_ids: list, user=None, is_run=False):
        """手工重试"""
        task_info = self.block.get_task_info()
        if not task_info:
            raise exception.ApiException(1001, "未查询任务信息！")
        # 为空激活所有失败子任务，有值激活指定失败子任务
        is_retry_all = False if subtask_ids else True
        if is_retry_all:
            subtask_ids = task_info.keys()
        jobs, log_msg = [], []
        for subtask_id in subtask_ids:
            subtask_info = json.loads(task_info[str(subtask_id)])
            if subtask_info.get('status') != task_enum.TaskStateEnum.ERROR.value:
                if not is_retry_all and user:
                    status = get_task_status_name(subtask_info.get('status'), False)
                    self.send_mq(self.task_id, error_msg=f'{user}重试: 当前子任务状态[{status}], 已不满足操作条件', subtask_id=subtask_id)
                continue
            atom_info = self.block.get_atom_info(subtask_id, subtask_info.get('current_step'))
            if atom_info.get('status') != task_enum.StepStateEnum.ERROR.value:
                if not is_retry_all and user:
                    status = get_task_status_name(atom_info.get('status'))
                    self.send_mq(self.task_id, error_msg=f'{atom_info.get("atom_name")}: {user}重试: 当前步骤状态[{status}], 不满足操作条件', subtask_id=subtask_id)
                continue
            meta = []
            if isinstance(atom_info.get('meta'), list):
                for i in atom_info.get('meta'):
                    i['status'] = task_enum.StepStateEnum.WAIT.value
                    meta.append({
                        'id': i.get('id'),
                        "statusKey": i.get("statusKey"),
                        'status': i.get('status')})
            atom_info.update(error_msg=None, status=task_enum.StepStateEnum.WAIT.value, pause_user=None)
            self.block.update_atom_info(subtask_id, subtask_info.get('current_step'), atom_info)
            subtask_info['status'] = task_enum.TaskStateEnum.PROCESS.value
            self.block.update_subtask_info(subtask_id, subtask_info)
            jobs = {
                'id': int(subtask_id),
                'status': subtask_info['status'],
                'steps': [{'id': subtask_info.get('current_step'), 'status': atom_info['status'], 'meta': meta}]}
            log_msg.append(f"[{subtask_id}] {atom_info.get('atom_name')}")
            if not is_run:
                continue
            """重试时检查被重试区服的当前步骤依赖任务是否是失败状态
            如果是失败状态让任务延迟几秒执行
            防止批量重试时被依赖区服任务先执行导致任务检查依赖不通过马上失败的问题"""
            depends = atom_info.get('before_depends')
            countdown = 0
            if depends and isinstance(depends, list):
                for i in depends:
                    if isinstance(i, dict) and i.get('subtask_id') and i.get('step'):
                        before_depend_atom_info = self.block.get_atom_info(i.get('subtask_id'), i.get('step'))
                        if before_depend_atom_info.get('status') == task_enum.StepStateEnum.ERROR.value:
                            countdown = 5
                            break
            tasks.atom_actuator_factory.apply_async((self.block.task_inst.id, subtask_id, subtask_info.get('current_step'), subtask_info.get('lifecycle')), countdown=countdown)
        if not jobs:
            raise exception.ApiException(1001, "暂无失败任务！")
        send_data = dict(jobs=jobs, status=task_enum.OrderStateEnum.Executing.value)
        if self.block.task_inst.status != task_enum.OrderStateEnum.Executing.value:
            self.block.task_inst.status = task_enum.OrderStateEnum.Executing.value
            send_data['steps'] = {'status': 'process', "step": [{"id": 3, "title": "执行"}]}
            db.session.commit()
        if user:
            if is_retry_all:
                send_data['error_msg'] = f"{user} 任务重试"
            elif len(log_msg) > 1:
                send_data['error_msg'] = f"{'、'.join(log_msg)}: {user}批量重试"
            else:
                send_data['error_msg'] = f"{log_msg.pop()}: {user}重新执行"
        self.send_mq(self.task_id, **send_data)

    def manual_init_start(self, task_inst):
        """初始化失败重新执行"""
        task_inst.status = task_enum.OrderStateEnum.Executing.value
        task_inst.session_id = str(uuid.uuid4())
        task_inst.sync_timestamp = int(time.time())
        if task_inst.type == 10:
            OpenPlan.query.filter(OpenPlan.task_id == task_inst.id).update({"status": task_inst.status})
        db.session.commit()
        tasks.task_actuator_factory.apply_async((task_inst.id, task_inst.sync_timestamp), task_id=task_inst.session_id)

    def manual_skip(self, params, user=None, is_run=False):
        """原子手工跳过"""
        for i in params:
            subtask_id, step = i['subtaskId'], i['step']
            subtask_info = self.block.get_subtask_info(subtask_id)
            if step != subtask_info.get('current_step'):
                if user:
                    self.send_mq(self.task_id, error_msg=f'{user}操作跳过，当前步骤不匹配不支持跳过', subtask_id=subtask_id)
                continue
            if subtask_info.get('status') == task_enum.TaskStateEnum.SUCCESS.value:
                if user:
                    self.send_mq(self.task_id, error_msg=f'{user}操作跳过，当前任务状态不支持跳过', subtask_id=subtask_id)
                continue
            atom_info = self.block.get_atom_info(subtask_id, step)
            if atom_info.get('status') not in (task_enum.StepStateEnum.ERROR.value, task_enum.StepStateEnum.PAUSE.value, task_enum.StepStateEnum.RETRYING.value, task_enum.StepStateEnum.PROCESS.value):
                if user:
                    self.send_mq(self.task_id, error_msg=f"{atom_info.get('atom_name')}: {user}操作跳过，当前步骤状态不支持跳过", subtask_id=subtask_id)
                continue
            if atom_info.get('skippable') != 1:
                if user:
                    self.send_mq(self.task_id, error_msg=f"{atom_info.get('atom_name')}: {user}操作跳过，当前步骤不支持跳过", subtask_id=subtask_id)
                continue
            atom_info.update(status=task_enum.StepStateEnum.SKIPPED.value, pause_user=None)
            self.block.update_atom_info(subtask_id, step, atom_info)
            self.subtask_executing(subtask_id)
            if user:
                self.send_mq(
                    self.task_id,
                    error_msg=f"{atom_info.get('atom_name')}: {user}跳过该步骤",
                    subtask_id=subtask_id,
                    jobs={'id': int(subtask_id), 'steps': [{'id': step, 'status': atom_info['status']}]})
            if not is_run:
                continue
            tasks.atom_actuator_factory.apply_async((self.block.task_inst.id, subtask_id, step, subtask_info.get('lifecycle')))
            # 激活被依赖任务并修改任务和步骤状态
            after_depends = atom_info.get('after_depends')
            if not isinstance(after_depends, list):
                continue
            for _i in after_depends:
                after_subtask_info = self.block.get_subtask_info(_i.get('subtask_id'))
                if after_subtask_info.get('current_step') == _i.get('step') and after_subtask_info.get('status') == task_enum.TaskStateEnum.ERROR.value:
                    after_atom_info = self.block.get_atom_info(_i.get('subtask_id'), _i.get('step'))
                    if after_atom_info.get('retry') != 1:
                        continue
                    after_atom_info['status'] = task_enum.StepStateEnum.WAIT.value
                    self.block.update_atom_info(_i.get('subtask_id'), _i.get('step'), after_atom_info)
                    after_subtask_info['status'] = task_enum.TaskStateEnum.PROCESS.value
                    self.block.update_subtask_info(_i.get('subtask_id'), after_subtask_info)
                    jobs = {
                        'id': int(_i.get('subtask_id')),
                        'status': task_enum.TaskStateEnum.PROCESS.value,
                        'steps': [{'id': _i.get('step'), 'status': task_enum.StepStateEnum.WAIT.value}]}
                    self.send_mq(self.task_id, jobs=jobs)
                    tasks.atom_actuator_factory.apply_async((self.block.task_inst.id, _i.get('subtask_id'),
                                                             _i.get('step'), after_subtask_info.get('lifecycle')))

    def manual_continue(self, subtask_ids: list, user=None, is_run=False):
        """任务继续执行
        subtask_ids: list 为空激活所有暂停状态子任务，有值激活指定区服暂停状态子任务
        """
        task_info = self.block.get_task_info()
        if not task_info:
            raise exception.ApiException(1001, "未查询任务信息！")
        is_start_all = False if subtask_ids else True
        if is_start_all:
            subtask_ids = [int(i) for i in task_info.keys()]
        send_data = {'jobs': [], 'status': task_enum.OrderStateEnum.Executing.value}
        if self.block.task_inst.status != task_enum.OrderStateEnum.Executing.value:
            send_data['steps'] = {'current': 2, 'status': 'process', "step": [{"id": 3, "title": "执行"}]}
            self.block.task_inst.status = task_enum.OrderStateEnum.Executing.value
            db.session.commit()
        for subtask_id in subtask_ids:
            subtask_info = json.loads(task_info[str(subtask_id)])
            if subtask_info.get('status') != task_enum.TaskStateEnum.PAUSE.value:
                if not is_start_all and user:
                    status = get_task_status_name(subtask_info.get('status'), False)
                    self.send_mq(self.task_id, error_msg=f'{user}继续执行：当前子任务状态[{status}], 不满足操作条件', subtask_id=subtask_id)
                continue
            atom_info = self.block.get_atom_info(subtask_id, subtask_info.get('current_step'))
            if atom_info.get('status') != task_enum.StepStateEnum.PAUSE.value:
                if not is_start_all and user:
                    status = get_task_status_name(atom_info.get('status'))
                    error_msg = f'{atom_info.get("name")}: {user}继续执行：当前步骤状态[{status}],不满足操作条件'
                    self.send_mq(self.task_id, error_msg=error_msg, subtask_id=subtask_id)
                continue
            subtask_info['status'] = task_enum.TaskStateEnum.PROCESS.value
            self.block.update_subtask_info(subtask_id, subtask_info)
            atom_info.update(
                end_time=storage_block.now_timestamp(),
                status=task_enum.StepStateEnum.SUCCESS.value,
                pause_user=None)
            self.block.update_atom_info(subtask_id, subtask_info.get('current_step'), atom_info)
            send_data['jobs'].append({
                'id': int(subtask_id),
                'status': subtask_info['status'],
                'steps': [{
                    'id': int(subtask_info.get('current_step')),
                    'status': atom_info['status'],
                    'endTime': atom_info['end_time']}]})
            if not is_run:
                continue
            tasks.atom_actuator_factory.apply_async((self.task_id, subtask_id, subtask_info.get('current_step'), subtask_info.get('lifecycle')))
        if not send_data['jobs']:
            raise exception.ApiException(1001, "暂无待继续执行的任务！")
        if user:
            if is_start_all:
                send_data.update(error_msg=f"暂停: {user}继续执行")
            elif len(subtask_ids) > 1:
                send_data.update(error_msg=f"{subtask_ids} 暂停: {user}批量继续执行")
            else:
                send_data.update(error_msg=f'暂停: {user}继续执行', subtask_id=subtask_ids.pop())
        self.send_mq(self.task_id, **send_data)

    def manual_pause(self, params: list, user, is_log=False):
        """手动中止多个子任务"""
        task_info = self.block.get_task_info()
        if not task_info:
            raise exception.ApiException(1001, "未查询任务信息！")
        logs_msg = {}
        for i in params:
            subtask_id, step = i['subtaskId'], i['step']
            subtask_info = json.loads(task_info[str(subtask_id)])
            if subtask_info.get("status") != task_enum.TaskStateEnum.PROCESS.value:
                if is_log:
                    status = get_task_status_name(subtask_info.get('status'), False)
                    logs_msg[subtask_id] = f"{user}中止该步骤失败: 当前子任务状态[{status}], 不满足操作条件"
                continue
            atom_info = self.block.get_atom_info(subtask_id, step)
            if subtask_info.get('current_step') != step or atom_info.get('status') not in (task_enum.StepStateEnum.RETRYING.value, task_enum.StepStateEnum.PROCESS.value):
                if is_log:
                    status = get_task_status_name(atom_info.get('status'))
                    logs_msg[subtask_id] = f"{atom_info.get('atom_name')}: {user}中止该步骤失败: 当前步骤状态[{status}], 不满足操作条件"
                continue
            if atom_info.get("pause_user"):
                # 已设置中止跳过
                if is_log:
                    logs_msg[subtask_id] = f"{atom_info.get('atom_name')}: {atom_info.get('pause_user')}已发起中止操作, {user}的操作被忽略"
                continue
            if is_log:
                logs_msg[subtask_id] = f"{atom_info.get('atom_name')}: {user}发起中止操作"
            atom_info.update(pause_user=user)
            self.block.update_atom_info(subtask_id, subtask_info.get('current_step'), atom_info)
        if logs_msg:
            logs, create_time = [], datetime.datetime.utcnow()
            _time = datetime_to_string(create_time)
            for i in logs_msg:
                task_log = TaskExecuteLog(task_id=self.task_id, context=logs_msg[i], world_id=i, create_time=create_time)
                db.session.add(task_log)
                db.session.flush()
                logs.append({
                    'id': task_log.id,
                    'time': _time,
                    'content': task_log.context,
                    'worldId': task_log.world_id})
            db.session.commit()
            self.send_mq(self.task_id, executeLogs=logs)
