# import re
import regex as re

# from ..identifier import Identifier
from mwcites.identifier import Identifier

PMTEMPLATE_RE = re.compile(r"\bpmid\s*=\s*(?:pmc)?([0-9]+)\b", re.I)
PMCTEMPLATE_RE = re.compile(r"\bpmc\s*=\s*(?:pmc)?([0-9]+)\b", re.I)

PMURL_RE = re.compile(r"//www\.ncbi\.nlm\.nih\.gov/pubmed/([0-9]+)\b", re.I)
PMCURL_RE = re.compile(r"//www\.ncbi\.nlm\.nih\.gov"
                       r"/pmc/articles/PMC([0-9]+)\b", re.I)


def extract(text):
    for match in PMTEMPLATE_RE.finditer(text):
        yield Identifier('pmid', match.group(1))

    for match in PMTEMPLATE_RE.finditer(text):
        yield Identifier('pmc', match.group(1))

    for match in PMURL_RE.finditer(text):
        yield Identifier("pmid", match.group(1))

    for match in PMCURL_RE.finditer(text):
        yield Identifier("pmc", match.group(1))
