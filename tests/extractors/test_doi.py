from wikidump.extractors import doi
from wikidump.extractors.common import Identifier

import pprint
import collections


INPUT_TEXT = """
This is a doi randomly placed in the text 10.0000/m1
Here's a typo that might be construed as a doi 10.60 people were there.
{{cite|...|doi=10.0000/m2|pmid=10559875}}
<ref>Halfaker, A., Geiger, R. S., Morgan, J. T., & Riedl, J. (2012).
The rise and decline of an open collaboration system: How Wikipedia’s
reaction to popularity is causing its decline.
American Behavioral Scientist,
0002764212469365 doi: 10.1177/0002764212469365</ref>.  Hats pants and banana
[http://dx.doi.org/10.1170/foo<bar>(herp)derp]
[http://dx.doi.org/10.1170/foo<bar>(herp)derp[waffles]]
{{cite|...|doi=10.1098/rspb.2008.1131|issue=1656}}
http://www.google.com/sky/#latitude=3.362&longitude=160.1238441&zoom=
10.2387/234310.2347/39423
<!--
    10.2387/234310.2347/39423-->
"""
EXPECTED = collections.Counter([
    Identifier('doi', "10.0000/m1"),
    Identifier('doi', "10.0000/m2"),
    Identifier('doi', "10.1177/0002764212469365"),
    Identifier('doi', "10.1170/foo<bar>(herp)derp"),
    Identifier('doi', "10.1170/foo<bar>(herp)derp[waffles]"),
    Identifier('doi', "10.1098/rspb.2008.1131"),
    Identifier('doi', "10.2387/234310.2347/39423"),
    Identifier('doi', "10.2387/234310.2347/39423")
])

"""
def test_extract_regex():
    ids = list(doi.extract_regex(INPUT_TEXT))
    pprint.pprint(ids)
    pprint.pprint(EXPECTED)
    eq_(ids, EXPECTED)

def test_extract_mwp():
    ids = list(doi.extract_mwp(INPUT_TEXT))
    pprint.pprint(ids)
    pprint.pprint(EXPECTED)
    eq_(ids, EXPECTED)
"""

# def test_extract():
#     ids = list(doi.extract(INPUT_TEXT))
#     pprint.pprint(ids)
#     pprint.pprint(EXPECTED)
#     eq_(ids, EXPECTED)

# def test_extract_island():
#     ids = list(doi.extract_island(INPUT_TEXT))
#     pprint.pprint(ids)
#     pprint.pprint(EXPECTED)
#     eq_(ids, EXPECTED)

# def test_extract_search():
#     ids = list(doi.extract_search(INPUT_TEXT))
#     pprint.pprint(ids)
#     pprint.pprint(EXPECTED)
#     #pprint.pprint(list(doi.tokenize_finditer(INPUT_TEXT)))
#     eq_(ids, EXPECTED)

def test_extract():
    captures = doi.extract(INPUT_TEXT)
    found_identifiers = collections.Counter(capture.data
        for capture in captures)

    assert found_identifiers == EXPECTED

    for _, (capture_begin, capture_end) in captures:
        print(_, capture_begin, capture_end)
        assert 0 <= capture_begin < len(INPUT_TEXT)
        assert 0 <= capture_end < len(INPUT_TEXT)
