import copy
from threading import RLock


class Snapshot:
    def __init__(self, id, data):
        self.id, self.data = id, copy.deepcopy(data)

    def to_dict(self):
        return copy.deepcopy(self.data)
