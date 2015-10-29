# import re
import regex as re

from ..identifier import Identifier

ISBN_RE = re.compile(r'isbn\s?=?\s?([0-9\-Xx]+)', re.I)


def extract(text):
    for match in ISBN_RE.finditer(text):
        id_ = match.group(1)
        yield Identifier(
            type='isbn',
            id=id_.replace('-', ''),
            raw=id_,
        )
