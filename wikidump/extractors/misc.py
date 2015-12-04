"""Various extractors."""
import functools

import regex
from more_itertools import peekable
from typing import Callable, Iterable, Iterator, List, TypeVar

from . import arxiv, doi, isbn, pubmed
from .common import CaptureResult, Span


class Section:
    """Section class."""
    def __init__(self, name: str, level: int, body: str):
        """Instantiate a section."""
        self.name = name
        self.level = level
        self.body = body
        self._full_body = None

    @property
    def is_preamble(self):
        """Return True when this section is the preamble of the page."""
        return self.level == 0

    @property
    def full_body(self) -> str:
        """Get the full body of the section."""
        if self._full_body is not None:
            return self._full_body

        if self.is_preamble:
            full_body = self.body
        else:
            equals = ''.join('=' for _ in range(self.level))
            full_body = '{equals}{name}{equals}\n{body}'.format(
                equals=equals,
                name=self.name,
                body=self.body,
            )
        self._full_body = full_body
        return full_body

    def __repr__(self):
        'Return a nicely formatted representation string'
        template = '{class_name}(name={name!r}, level={level!r}, body={body!r}'
        return template.format(
            class_name=self.__class__.__name__,
            name=self.name,
            level=self.level,
            body=self.body[:20],
        )


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


def sections(source: str, include_preamble: bool=False) -> Iterator[CaptureResult[Section]]:
    """Return the sections found in the document."""
    section_header_matches = peekable(section_header_re.finditer(source))
    if include_preamble:
        try:
            body_end = section_header_matches.peek().start()
            body_end -= 1  # Don't include the newline before the next section
        except StopIteration:
            body_end = len(source)
        preamble = Section(
            name='',
            level=0,
            body=source[:body_end],
        )
        yield CaptureResult(preamble, Span(0, body_end))

    for match in section_header_matches:
        name = match.group('section_name')
        level = len(match.group('equals'))

        body_begin = match.end() + 1  # Don't include the newline after
        try:
            body_end = section_header_matches.peek().start()
            body_end -= 1  # Don't include the newline before the next section
        except StopIteration:
            body_end = len(source)

        section = Section(
            name=name,
            level=level,
            body=source[body_begin:body_end],
        )

        yield CaptureResult(section, Span(match.start(), body_end))


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
