import copy
from threading import RLock


class Snapshot:
    def __init__(self, id, data):
        self.id, self.data = id, copy.deepcopy(data)
