import collections
import functools
from more_itertools import peekable

import regex

from .. import utils, languages
from . import arxiv, pubmed, doi, isbn
from .common import CaptureResult, Span

Section = collections.namedtuple('Section', 'name level body')

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
def _pattern_or(words):
    words_joined = '|'.join(words)

    return r'(?:{})'.format(words_joined)


def references(source):
    pattern = regex.compile(
        r'''
            <ref
            .*?
            <\/ref>
        ''', regex.VERBOSE | regex.IGNORECASE | regex.DOTALL)

    for match in pattern.finditer(source):
        yield CaptureResult(match.group(0), Span(*match.span()))


def sections(source):
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


# TODO: instead of comparing section_name to a bib synonym,
# search all the possible bib synonyms in the section name
@functools.lru_cache(maxsize=500)
def is_secion_bibliography(section_name, language):
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


def templates(source):
    for match in templates_re.finditer(source):
        yield CaptureResult(match.group(0), Span(*match.span()))


def pub_identifiers(source, extractors=None):
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
