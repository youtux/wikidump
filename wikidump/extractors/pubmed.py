"""
Regular expressions taken from `python-mwcites` by Aaron Halfaker.
See https://github.com/mediawiki-utilities/python-mwcites
"""

import regex as re

from .common import CaptureResult, Identifier, Span

__all__ = ['extract']

PMID_TEMPLATE_RE = re.compile(r"\bpmid\s*=\s*(?:pmc)?([0-9]+)\b", re.I)
PMC_TEMPLATE_RE = re.compile(r"\bpmc\s*=\s*(?:pmc)?([0-9]+)\b", re.I)

PMID_URL_RE = re.compile(r"//www\.ncbi\.nlm\.nih\.gov/pubmed/([0-9]+)\b", re.I)
PMC_URL_RE = re.compile(r"//www\.ncbi\.nlm\.nih\.gov"
                       r"/pmc/articles/PMC([0-9]+)\b", re.I)


def extract(text):
    for pmid_re in (PMID_TEMPLATE_RE, PMID_URL_RE):
        for match in pmid_re.finditer(text):
            id_ = match.group(1)
            span = match.span(1)
            yield CaptureResult(
                Identifier('pmid', id_), Span(*span))

    for pmc_re in (PMC_TEMPLATE_RE, PMC_URL_RE):
        for match in pmc_re.finditer(text):
            id_ = match.group(1)
            span = match.span(1)
            yield CaptureResult(
                Identifier('pmc', id_), Span(*span))
