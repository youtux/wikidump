import collections
import functools

import regex

from . import utils

Reference = collections.namedtuple('Reference', 'text')
Section = collections.namedtuple('Section', 'name level')


@functools.lru_cache(maxsize=10)
@utils.listify
def references(source):
    pattern = regex.compile(r'(?P<ref><ref>.+?<\/ref>)',
        regex.VERBOSE | regex.MULTILINE)

    for match in pattern.finditer(source):
        yield Reference(text=match.group('ref'))


@functools.lru_cache(maxsize=10)
@utils.listify
def sections(source):
    pattern = regex.compile(
        r'''^
            (?P<equals>=+)              # Match the equals, greedy
            (?P<section_name>           # <section_name>:
                .+?                     # Text inside, non-greedy
            )
            (?P=equals)\s*              # Re-match the equals
            $
        ''', regex.VERBOSE | regex.MULTILINE)
    for match in pattern.finditer(source):
        yield Section(
            name=match.group('section_name'),
            level=len(match.group('equals')),
        )


@functools.lru_cache(maxsize=10)
@utils.listify
def bibliography(source):
    # Exit immediately if there is no section named 'bibliography'
    if 'bibliography' not in (sect.name.lower() for sect in sections(source)):
        return None

    pattern = regex.compile(
        r'''
            (?P<equals>=+)              # Match the equals
                \s*(?i)bibliography\s*  # Match the 'bibliography' (case-ins)
            (?P=equals)                 # Re-match the equals
            \s*\n                       # Consume any whitespace and the \n
            (?P<text>(?s)
                .*?                     # Text of the bibliography
            )
            (?:=+|$)                    # Finish when you find a new section
                                        # or the end of document
        ''', regex.VERBOSE)

    for match in pattern.finditer(source):
        yield match.group('text')
