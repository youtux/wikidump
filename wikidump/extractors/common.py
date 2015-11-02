import collections

CaptureResult = collections.namedtuple('CaptureResult', 'data span')
Identifier = collections.namedtuple("Identifier", ['type', 'id'])


class Span(collections.namedtuple('Span', 'begin end')):

    def __le__(self, other):
        # return self.begin >= other.begin and self.end <= other.end
        # HACK: the following is more efficient. Sorry :(
        return self[0] >= other[0] and self[1] <= other[1]

    def __lt__(self, other):
        return self[0] > other[0] and self[1] < other[1]
