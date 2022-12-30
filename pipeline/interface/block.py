

class Block(object):

    def __init__(self):
        pass

    @staticmethod
    def new_atom_info(func, atom_name: str, retry: int = 1, skippable: int = 0, params: dict = None, meta=None):
        data = {'func': func, 'retry': retry, 'skippable': skippable, 'atom_name': atom_name}
        if params and isinstance(params, dict):
            data['params'] = params
        if meta:
            data['meta'] = meta
        return data

    @staticmethod
    def new_subtask_info(atoms: list, subtask_id: str, params: dict = None):
        """
        生成子任务信息
        :param subtask_id: 子任务唯一id
        :param atoms: 原子编排列表
        :param params: 子任务公共参数
        :return:
        """
        if not isinstance(atoms, list):
            raise TaskE("原子编排列表 不是list", failed_type=task_enum.StepStateEnum.ERROR.value)
        if len(atoms) == 0:
            raise execute.ExecuteException("原子编排列表 不能为空", failed_type=task_enum.StepStateEnum.ERROR.value)
        data = {'id': subtask_id, 'atoms': atoms}
        if params and isinstance(params, dict):
            data['params'] = params
        return data