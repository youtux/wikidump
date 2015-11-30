"""Extractor for "isbn" identifiers.

Regular expression taken from `python-mwcites` by Aaron Halfaker.
See https://github.com/mediawiki-utilities/python-mwcites
"""
from typing import Iterator

import regex as re

from .common import CaptureResult, Identifier, Span

__all__ = ('extract',)

ISBN_RE = re.compile(r'isbn\s?=?\s?([0-9\-Xx]+)', re.I)


def extract(text: str) -> Iterator[CaptureResult[Identifier]]:
    """Extract isbn identifiers."""
    for match in ISBN_RE.finditer(text):
        id_ = match.group(1)
        span = match.span(1)
        yield CaptureResult(
            Identifier('isbn', id=id_.replace('-', '')), Span(*span))
