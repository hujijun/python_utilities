from queue import LifoQueue, SimpleQueue

# 先进后出
queue = SimpleQueue()

queue.put(11)
queue.put("aaa")
queue.put(12)


# while True:
#     print(queue.get())
#     print(queue.qsize())
