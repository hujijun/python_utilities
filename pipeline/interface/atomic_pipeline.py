def get_definition_atomic_choreography(self) -> list:
    """获取定义的原子编排, 校验定义原子编排"""
    subtask_info_list = self.definition_atomic_choreography()
    if not isinstance(subtask_info_list, list):
        raise execute.ExecuteException("定义的原子编排格式错误", failed_type=task_enum.StepStateEnum.ERROR.value)
    if len(subtask_info_list) == 0:
        raise execute.ExecuteException("定义的原子编排为空", failed_type=task_enum.StepStateEnum.ERROR.value)
    for subtask_info in subtask_info_list:
        if not (isinstance(subtask_info, dict) and isinstance(subtask_info.get('atoms'), list)):
            raise execute.ExecuteException("定义的原子编排格式错误", failed_type=task_enum.StepStateEnum.ERROR.value)
        if len(subtask_info.get('atoms')) == 0:
            raise execute.ExecuteException("定义的步骤为空", failed_type=task_enum.StepStateEnum.ERROR.value)
    return subtask_info_list