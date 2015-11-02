import collections

Span = collections.namedtuple('Span', 'begin end')
CaptureResult = collections.namedtuple('CaptureResult', 'data span')
Identifier = collections.namedtuple("Identifier", ['type', 'id'])
