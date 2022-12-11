from flatbuffers import builder
from POFlat import AtomPo

AtomPo.AddFunc()

class aa(object):
    model = AtomPo

    def to_bytes(self, hp, name) -> bytearray:
        b = builder.Builder(0)
        xx = b.CreateString(name)
        b.StartObject(3)
        self.model.(b, hp)
        self.model.AddName(b, xx)
        b.Finish(b.EndObject())
        return b.Output()

    def to_class(self, b):
        return self.model.AtomPo.GetRootAs(b)


cccc = aa()
vvv = cccc.to_bytes(23, '工工要')
print(vvv)
ddd = cccc.to_class(vvv)
print(ddd.Name().decode())
print(ddd.Hp())