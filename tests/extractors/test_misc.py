from wikidump.extractors.misc import Section, sections

import collections

INPUT_TEXT = '''
Garbage

= Section 1 =
Lorem ipsum
lorem ipsummmm

== Section 2 ==
asdnot
 dsa
 datad

 def a():
     pass
ddase
s
'''
EXPECTED = collections.Counter([
    Section(name=' Section 1 ', level=1, body='''\
Lorem ipsum
lorem ipsummmm
'''
    ),
    Section(name=' Section 2 ', level=2, body='''\
asdnot
 dsa
 datad

 def a():
     pass
ddase
s
'''
    ),
])


def test_extract():
    captures = sections(INPUT_TEXT)
    found_sections = collections.Counter(capture.data
        for capture in captures)

    assert found_sections == EXPECTED

    for _, (capture_begin, capture_end) in captures:
        assert 0 <= capture_begin <= len(INPUT_TEXT)
        assert 0 <= capture_end <= len(INPUT_TEXT)
