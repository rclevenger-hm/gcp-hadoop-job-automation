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

    def start_after(self, cursor):
        return Query(self.db, self.filters, self.orders, self.maximum, cursor)

    def stream(self, **kwargs):
        rows = list(self.db.data.items())
        for f in self.filters:
            rows = [(id, d) for id, d in rows if f.field_path in d and (d[f.field_path] == f.value if f.op_string == '==' else d[f.field_path] <= f.value)]
        for field, direction in reversed(self.orders):
            rows.sort(key=lambda r: r[0] if field == '__name__' else r[1][field], reverse=direction == 'DESCENDING')
        if self.cursor:
            key = (self.cursor['created_at'], self.cursor['__name__'].id)
            rows = [(id, d) for id, d in rows if (d['created_at'], id) < key]
        return [Snapshot(id, d) for id, d in rows[:self.maximum]]


class Transaction:
    def __init__(self, db):
        self.db, self.pending = db, []

    def set(self, ref, data):
        self.pending.append((ref.id, copy.deepcopy(data)))

    def create(self, ref, data):
        assert ref.id not in self.db.data
        self.set(ref, data)
