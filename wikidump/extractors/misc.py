"""Various extractors."""
import functools

import regex
from more_itertools import peekable
from typing import Callable, Iterable, Iterator, List, NamedTuple, TypeVar

from . import arxiv, doi, isbn, pubmed
from .. import languages
from .common import CaptureResult, Span

Section = NamedTuple('Section', [
    ('name', str),
    ('level', int),
    ('body', str),
])

section_header_re = regex.compile(
    r'''^
        (?P<equals>=+)              # Match the equals, greedy
        (?P<section_name>           # <section_name>:
            .+?                     # Text inside, non-greedy
        )
        (?P=equals)\s*              # Re-match the equals
        $
    ''', regex.VERBOSE | regex.MULTILINE)

templates_re = regex.compile(
    r'''
        \{\{
        (?P<content>(?s).*?)
        \}\}
    ''', regex.VERBOSE)


@functools.lru_cache(maxsize=1000)
def _pattern_or(words: List) -> str:
    words_joined = '|'.join(words)

    return r'(?:{})'.format(words_joined)


def references(source: str) -> Iterator[CaptureResult[str]]:
    """Return all the references found in the document."""
    pattern = regex.compile(
        r'''
            <ref
            .*?
            <\/ref>
        ''', regex.VERBOSE | regex.IGNORECASE | regex.DOTALL)

    for match in pattern.finditer(source):
        yield CaptureResult(match.group(0), Span(*match.span()))


def sections(source: str) -> Iterator[CaptureResult[Section]]:
    """Return the sections found in the document."""
    section_header_matches = peekable(section_header_re.finditer(source))
    for match in section_header_matches:
        name = match.group('section_name')
        level = len(match.group('equals'))

        body_begin = match.end() + 1  # Don't include the newline after
        try:
            body_end = (section_header_matches.peek().start()
                        - 1  # Don't include the newline before
                       )
        except StopIteration:
            body_end = len(source)

        section = Section(
            name=name,
            level=level,
            body=source[body_begin:body_end],
            # body="",
        )

        yield CaptureResult(section, Span(match.start(), body_end))


@functools.lru_cache(maxsize=500)
def is_secion_bibliography(section_name: str, language: str) -> bool:
    """Check if a section name is a bibliography."""
    bibliography_synonyms = languages.bibliography[language]
    return section_name.strip().lower() in bibliography_synonyms


# @functools.lru_cache(maxsize=10)
# @utils.listify
# def citations(source, language):
#     citation_synonyms = languages.citation[language]

#     citation_synonyms_pattern = _pattern_or(citation_synonyms)

#     pattern = regex.compile(
#         r'''
#             \{\{
#             \s*
#             %s
#             \s+
#             (?:(?s).*?)
#             \}\}
#         ''' % (citation_synonyms_pattern,), regex.VERBOSE
#     )

#     for match in pattern.finditer(source):
#         yield match.group(0)


def templates(source: str) -> Iterator[CaptureResult[str]]:
    """Return all the templates found in the document."""
    for match in templates_re.finditer(source):
        yield CaptureResult(match.group(0), Span(*match.span()))

T = TypeVar('T')
Extractor = Callable[[str], T]
def pub_identifiers(source: str, extractors: Iterable[Extractor]=None) -> T:
    """Return all the identifiers found in the document."""
    if extractors is None:
        extractors = (
            arxiv.extract,
            doi.extract,
            isbn.extract,
            pubmed.extract,
        )
    for identifier_extractor in extractors:
        for capture in identifier_extractor(source):
            yield capture
