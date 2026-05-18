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


class Query:
    def __init__(self, db, filters=(), orders=(), maximum=10000, cursor=None):
        self.db, self.filters, self.orders, self.maximum, self.cursor = db, filters, orders, maximum, cursor

    def document(self, id):
        return Reference(self.db, id)

    def where(self, *, filter):
        return Query(self.db, (*self.filters, filter), self.orders, self.maximum, self.cursor)

    def order_by(self, name, direction='ASCENDING'):
        return Query(self.db, self.filters, (*self.orders, (name, direction)), self.maximum, self.cursor)

    def limit(self, count):
        return Query(self.db, self.filters, self.orders, count, self.cursor)
