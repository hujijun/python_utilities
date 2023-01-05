
class Item(object):
    def __init__(self, _type):
        self._type = _type

    def __set__(self, instance, value):
        print(instance)
        print(value)

    def __get__(self, instance, owner):
        print(instance)
        print(owner)



class AtomPo(object):
    status = Item(int)


AtomPo.status = 1

print(AtomPo.status)

