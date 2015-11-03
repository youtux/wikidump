# import re
import regex as re

from .common import CaptureResult, Identifier, Span

__all__ = ['extract']

# From http://arxiv.org/help/arxiv_identifier
old_id_pattern = r"-?(?P<old_id>(?:[a-z]+(.[a-z]+)/)?[0-9]{4}[0-9]+)"
new_id_pattern = r"(?P<new_id>[0-9]{4}.[0-9]+)(?:v[0-9]+)?"

prefixes = [r"arxiv\s*=\s*", r"//arxiv\.org/(abs/)?", r"arxiv:\s?"]

ARXIV_REs = [re.compile(
                r'(?:{prefix})(?:{old_id_pattern}|{new_id_pattern})'.format(
                    prefix=prefix,
                    old_id_pattern=old_id_pattern,
                    new_id_pattern=new_id_pattern,
                ), re.I | re.U)
             for prefix in prefixes]


def extract(text):
    for pattern in ARXIV_REs:
        for match in pattern.finditer(text):
            if match.group('new_id'):
                id_ = match.group('new_id')
                span = match.span('new_id')
            else:
                id_ = match.group('old_id')
                span = match.span('old_id')

            yield CaptureResult(
                Identifier("arxiv", id=id_.lower()), Span(*span))
