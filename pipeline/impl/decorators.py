
def order_lock(func):
    """工单锁装饰器"""
    def wrapper(self, *args, **kwargs):
        lock_key = f"lock_{self.task_inst.session_id}"
        lock_uuid = redis_service.get_lock(lock_key, _time=300)
        func(self, *args, **kwargs)
        # 解锁
        redis_service.unlock(lock_key, lock_uuid)
    return wrapper
