import copy
from threading import RLock


class Snapshot:
    def __init__(self, id, data):
        self.id, self.data = id, copy.deepcopy(data)

    def to_dict(self):
        return copy.deepcopy(self.data)


class Reference:
    def __init__(self, db, id):
        self.db, self.id = db, id

    def get(self, **kwargs):
        return Snapshot(self.id, self.db.data.get(self.id))
