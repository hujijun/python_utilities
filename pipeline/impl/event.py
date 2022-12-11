from pipeline.interface.event import TaskEventListenerInterface


class TaskEventListener1(TaskEventListenerInterface):

    def start(self):
        print("任务开始了1")

    def completed(self):
        print("任务完成1")


class TaskEventListener2(TaskEventListenerInterface):

    def start(self):
        print("任务开始了2")

    def completed(self):
        print("任务完成2")


class TaskEventDispatch(object):
    """事件分发器"""

    def __init__(self):
        # 事件监听列表
        # self.event_listeners = defaultdict(list)
        self.event_listeners = []

    def dispatch(self, callback):
        """派发"""
        for listener in self.event_listeners:
            if hasattr(listener, callback.__name__):
                getattr(listener, callback.__name__)()

    def add_listener(self, listener: TaskEventListenerInterface):
        """添加事件监听"""
        self.event_listeners.append(listener)

    def remove_listener(self, listener: TaskEventListenerInterface):
        """移除事件监听"""
        self.event_listeners.remove(listener)
