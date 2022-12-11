
class AtomInterface(object):
    """原子接口"""

    def execute(self, *args, **kwargs):
        """执行"""

    def is_ok(self) -> bool:
        """检查是否执行成功"""
        return True

    def execute_error(self):
        """执行出错"""

    def execute_success(self):
        """执行成功"""


class DockerStart(AtomInterface):

    def execute(self, *args, **kwargs):
        """"""



class AtomExecute(object):
    """原子执行器"""

    def __init__(self, atom: AtomInterface):
        self.atom = atom

    def run(self):
        try:
            self.atom.execute()
        except Exception:
            self.atom.execute_error()
