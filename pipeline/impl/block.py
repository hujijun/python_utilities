import json
import time
from model import TaskVo
from pipeline.redis_service import RedisService

now_timestamp = lambda: int(time.time())


class RedisBlock(RedisService):
    """任务数据基于redis实现"""

    def __init__(self, task_id: int, url):
        # 子任务执行列表 key
        super().__init__(url)
        self.order_key = f"task_status:{task_id}:main"
        # 原子执行列表 前缀 key
        self.task_key_prefix = f"task_status:{task_id}:atoms_"
        self.task_id = task_id
        self._task_info = None

    @property
    def task_info(self) -> dict:
        """获取工单的所有子任务"""
        if self._task_info is None:
            self._task_info = self.conn.hgetall(self.order_key)
        return self._task_info

    def get_all_atom_info(self, subtask_id: str) -> dict:
        """ 获取子任务的所有步骤
        :param subtask_id: 子任务id 也是区服id
        :return: {b"1": "{}"}
        """
        return self.conn.hgetall(f"{self.task_key_prefix}{subtask_id}")

    def get_atom_info(self, subtask_id: str, step: int) -> dict:
        """获取原子数据"""
        try:
            result = self.conn.hget(f"{self.task_key_prefix}{subtask_id}", step)
            result = json.loads(result)
            return result
        except Exception as error:
            utils.logger.exception(error)
            raise execute.ExecuteException('获取原子数据出错, world_id: %s step: %s' % (subtask_id, step),
                                           failed_type=task_enum.StepStateEnum.ERROR.value)

    def get_subtask_info(self, subtask_id) -> dict:
        """获取子任务数据"""
        try:
            result = self.conn.hget(self.order_key, subtask_id)
            result = json.loads(result)
            return result
        except Exception as error:
            utils.logger.exception(error)
            raise execute.ExecuteException('获取子任务数据出错', failed_type=task_enum.StepStateEnum.ERROR.value)

    def update_atom_info(self, subtask_id: str, step_number: int, data: dict):
        """更新原子数据"""
        self.hset(f"{self.task_key_prefix}{subtask_id}", step_number, json.dumps(data))

    def update_subtask_info(self, subtask_id: str, data: dict):
        self.hset(f"{self.order_key}", subtask_id, json.dumps(data))

    def edit_atom_info(self, subtask_id: str, step_number: int, data: dict):
        """覆盖更新"""
        atom_info = self.get_atom_info(subtask_id, step_number)
        atom_info.update(data)
        self.update_atom_info(subtask_id, step_number, atom_info)

    def init_set_task_info(self, subtask_info_list):
        """初始化生成任务执行数据"""
        # 初始化前 清空任务数据
        self.clear_task_info()
        subtasks = {}
        for subtask_info in subtask_info_list:
            data = {
                'total_steps': len(subtask_info.get('atoms')),  # 子任务总步骤数
                'start_time': now_timestamp(),
                'current_step': 1,  # 当前步骤，默认从一步开始
                'lifecycle': 0,
                'status': task_enum.TaskStateEnum.WAIT.value  # 主任务状态默认待执行
            }
            if isinstance(subtask_info.get('params'), dict):
                data['params'] = subtask_info.get('params')
            subtask_id = str(subtask_info.get('id'))
            # self.redis_service.hset(self.order_key, subtask_id, json.dumps(data))
            subtasks[subtask_id] = json.dumps(data)
            atom_dict = {}
            for k in range(len(subtask_info.get('atoms'))):
                atom = subtask_info.get('atoms')[k]
                data = {
                    'func': atom.get('func').name,
                    'retry': atom.get('retry'),
                    'retry_count': 0,
                    'timeout_count': 0,
                    'depend_fail_count': 0,
                    'skippable': atom.get('skippable'),
                    'atom_name': atom.get('atom_name'),
                    'meta': atom.get('meta'),
                    'status': task_enum.StepStateEnum.WAIT.value}
                if atom.get('before_depends'):
                    data['before_depends'] = atom.get('before_depends')
                if atom.get('after_depends'):
                    data['after_depends'] = atom.get('after_depends')
                if atom.get('params'):
                    data['params'] = atom.get('params')
                atom_dict[k + 1] = json.dumps(data)
                # self.redis_service.hset(f"{self.task_key_prefix}{subtask_id}", k + 1, json.dumps(data))
            self.redis_service.hmset(f"{self.task_key_prefix}{subtask_id}", atom_dict)
        self.redis_service.hmset(self.order_key, subtasks)

    def clear_task_info(self):
        """清除任务执行数据"""
        utils.logger.info(f"[{self.task_inst.id}] 清除任务执行数据")
        task_info = self.conn.hgetall(self.order_key)
        for subtask_id in task_info:
            if isinstance(subtask_id, bytes):
                subtask_id = str(subtask_id, encoding='utf8')
            self.delete(f"{self.task_key_prefix}{subtask_id}")
        if self.conn.exists(f"task_status:{self.task_inst.id}:preconditions"):
            # 检查key存在时再执行删除操作，防止初始化前和任务执行成功后重复执行删除操作，如果seq先删除会导致数据同步指令积压的情况
            self.delete(f"task_status:{self.task_inst.id}:preconditions")
        self.delete(self.order_key)
        return task_info

    def get_uuid(self, subtask_id, step, lifecycle):
        return f"{self.task_id}:{subtask_id}:{step}:{lifecycle}"
