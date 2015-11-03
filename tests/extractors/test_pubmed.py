from wikidump.extractors import pubmed
from wikidump.extractors.common import Identifier

import collections


def test_extract():
    text = """
    This is some text with a template cite. {{cite|...|...|pmid=1}}.
    This is some text with a template cite. {{cite|...|...|pmid = 2|...}}.
    This is some text with a template cite. {{cite|...|...|pmc = 3|...}}.
    This is some text with a template cite. {{cite|...|...|pmc = pmc4|...}}.
    This is some text with a link [http://www.ncbi.nlm.nih.gov/pubmed/5 ID]
    Another link [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6 ID]
    """
    captures = list(pubmed.extract(text))
    expected = collections.Counter([
        Identifier('pmid', "1"),
        Identifier('pmid', "2"),
        Identifier('pmc', "3"),
        Identifier('pmc', "4"),
        Identifier('pmid', "5"),
        Identifier('pmc', "6")
    ])

    found_identifiers = collections.Counter(capture.data
        for capture in captures)

    assert found_identifiers == expected

    for _, (capture_begin, capture_end) in captures:
        assert 0 <= capture_begin < len(text)
        assert 0 <= capture_end < len(text)
