import collections
import functools

import regex

from . import utils, languages

# Reference = collections.namedtuple('Reference', 'text')
Section = collections.namedtuple('Section', 'name level')


def _pattern_or(words):
    words_joined = '|'.join(words)

    return r'(?:{})'.format(words_joined)


@functools.lru_cache(maxsize=10)
@utils.listify
def references(source):
    pattern = regex.compile(
        r'''
            <ref
            .*?
            <\/ref>
        ''', regex.VERBOSE | regex.MULTILINE)

    for match in pattern.finditer(source):
        yield match.group(0)


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
def bibliography(source, language):
    # Exit immediately if there is no section named 'bibliography'
    bibliography_t = languages.bibliography[language]
    if bibliography_t not in (sect.name.lower() for sect in sections(source)):
        return None

    pattern = regex.compile(
        r'''
            (?P<equals>=+)              # Match the equals
                \s*(?i){bibliography_t}
                \s*                     # Match the 'bibliography' (case-ins)
            (?P=equals)                 # Re-match the equals
            \s*\n                       # Consume any whitespace and the \n
            (?P<text>(?s)
                .*?                     # Text of the bibliography
            )
            (?:=+|$)                    # Finish when you find a new section
                                        # or the end of document
        '''.format(bibliography_t=bibliography_t), regex.VERBOSE)

    for match in pattern.finditer(source):
        yield match.group('text')


@functools.lru_cache(maxsize=10)
@utils.listify
def citations(source, language):
    citation_synonyms = languages.citation[language]

    citation_synonyms_pattern = _pattern_or(citation_synonyms)

    pattern = regex.compile(
        r'''
            \{\{
            \s*
            %s
            \s+
            (?:(?s).*?)
            \}\}
        ''' % (citation_synonyms_pattern,), regex.VERBOSE
    )

    for match in pattern.finditer(source):
        yield match.group(0)


@functools.lru_cache(maxsize=10)
@utils.listify
def templates(source):
    pattern = regex.compile(
        r'''
            \{\{
            (?P<content>.*?)
            \}\}
        ''', regex.VERBOSE | regex.MULTILINE)

    for match in pattern.finditer(source):
        yield match.group(0)
