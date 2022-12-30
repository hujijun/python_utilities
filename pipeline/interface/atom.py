import abc


class AtomInterface(object):
    """原子接口"""

    @property
    def timeout(self) -> int:
        """步骤执行超时时间，默认为5分钟"""
        return 5 * 60

    @property
    def timeout_count(self) -> int:
        """超时次数退出"""
        return 2

    @property
    def timeout_task_interval(self) -> int:
        """发送超时任务间隔时间"""
        return 2 * 60

    @property
    def retry_task_interval(self) -> int:
        """发送重试任务间隔时间"""
        return 2 * 60

    @property
    def retry_count(self) -> int:
        """失败重试总次数退出任务，  -1 不跳出"""
        return 3

    @property
    def is_next(self) -> bool:
        """原子执行完，可以执行下一步"""
        return False

    def __init__(self, task_engine, step: int, atom_info: dict):
        self.task_engine = task_engine
        # 原子信息
        self.atom_info = atom_info
        # 打印日志前缀
        self.log_prefix = f"{self.task_engine.task_name}[{self.task_inst.id}:{subtask_id}:{step}:{self.subtask_info.get('lifecycle')}] {self.atom_info.get('atom_name')}:"

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        """原子执行逻辑"""
        raise NotImplementedError

    @abc.abstractmethod
    def execute_error(self):
        """执行失败后，需要执行的逻辑"""

    @abc.abstractmethod
    def execute_success(self, status):
        """执行成功后，需要执行的逻辑"""
