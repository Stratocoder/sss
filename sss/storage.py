from collections import deque


class Index(object):
    pass


class OrderedIndex(Index):
    pass


class UnorderedIndex(Index):
    pass


class Storage(object):
    def __init__(self):
        self._data = deque()
        self._indexes = {}

    def add_ordered_index(self, field):
        self._indexes[field] = OrderedIndex()

    def add_unordered_index(self, field):
        self._indexes[field] = UnorderedIndex()

    def insert(self, record):
        for field, index in self._indexes:
            index.index(record[field], len(self._data))
        self._data.append(record)

    def get(self, **kwargs):
        if not kwargs:
            raise ValueError('Query arguments missing')
        for field, value in kwargs.iteritems():
            pass
