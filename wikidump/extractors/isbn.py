# import re
import regex as re

from .common import CaptureResult, Identifier, Span
from .. import utils

ISBN_RE = re.compile(r'isbn\s?=?\s?([0-9\-Xx]+)', re.I)



def extract(text):
    for match in ISBN_RE.finditer(text):
        id_ = match.group(1)
        span = match.span(1)
        yield CaptureResult(
            Identifier('isbn', id=id_.replace('-', '')), Span(*span))
