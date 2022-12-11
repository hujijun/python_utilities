"""
事件源发布一个事件
事件监听器可以消费这个事件
事件源：事件的触发者，比如上面的注册器就是事件源。
事件：描述发生了什么事情的对象，比如上面的：xxx注册成功的事件
事件监听器：监听到事件发生的时候，做一些处理，比如上面的：路人A、路人B
"""


class EventInterface(object):
    """事件对象"""

    def __init__(self, source):
        self.source = source


class TaskEventListenerInterface(EventInterface):
    """任务事件监听器"""

    def start(self):
        pass

    def completed(self):
        pass

    def error(self):
        pass

