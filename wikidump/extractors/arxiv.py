"""Extractor for "arxiv" identifiers.

Regular expressions taken from `python-mwcites` by Aaron Halfaker.
See https://github.com/mediawiki-utilities/python-mwcites
"""
from typing import Iterator

import regex as re

from .common import CaptureResult, Identifier, Span

__all__ = ('extract',)

# From http://arxiv.org/help/arxiv_identifier
old_id_pattern = r"-?(?P<old_id>(?:[a-z]+(.[a-z]+)/)?[0-9]{4}[0-9]+)"
new_id_pattern = r"(?P<new_id>[0-9]{4}.[0-9]+)(?:v[0-9]+)?"

prefixes = [r"arxiv\s*=\s*", r"//arxiv\.org/(abs/)?", r"arxiv:\s?"]

all_re = r'(?:{prefix})(?:{old_id_pattern}|{new_id_pattern})'

ARXIV_REs = [all_re.format(prefix=prefix,
                           old_id_pattern=old_id_pattern,
                           new_id_pattern=new_id_pattern,
                           )
             for prefix in prefixes]

ARXIV_REs = [re.compile(el, re.I | re.U) for el in ARXIV_REs]


def extract(text: str) -> Iterator[CaptureResult[Identifier]]:
    """Extract arxiv identifiers."""
    for pattern in ARXIV_REs:
        for match in pattern.finditer(text):
            if match.group('new_id'):
                id_ = match.group('new_id')
                span = match.span('new_id')
            else:
                id_ = match.group('old_id')
                span = match.span('old_id')

            yield CaptureResult(
                Identifier("arxiv", id=id_.lower()), Span(*span)
            )
