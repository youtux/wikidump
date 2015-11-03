from wikidump.extractors.misc import Section, sections, templates

from .utils import assert_captures_in_text

from textwrap import dedent


def test_sections():
    text = dedent('''\
        Garbage

        = Section 1 =
        Lorem ipsum
        lorem ipsummmm

        == Section 2 ==
        asdnot
         dsa
         datad
        ''')

    expected = [
        Section(name=' Section 1 ', level=1, body=dedent('''\
            Lorem ipsum
            lorem ipsummmm
            ''')
        ),
        Section(name=' Section 2 ', level=2, body=dedent('''\
            asdnot
             dsa
             datad
            ''')
        ),
    ]

    captures = list(sections(text))
    found_sections = [capture.data for capture in captures]

    assert found_sections == expected

    assert_captures_in_text(captures, text)


def test_oneline_template():
    text = dedent('''\
        {{cite journal |vauthors = Poland GA, Jacobson RM | title = The Age-Old Struggle against the Antivaccinationists | journal = N Engl J Med | volume = 364 | pages = 97–9 | date = 13 January 2011 | pmid = 21226573 | doi = 10.1056/NEJMp1010594 | url = http://www.nejm.org/doi/full/10.1056/NEJMp1010594 | archiveurl = http://web.archive.org/web/20140423082318/http://www.nejm.org/doi/full/10.1056/NEJMp1010594 | archivedate = 23 April 2014 }}''')
    captures = list(templates(text))

    found_templates = [capture.data for capture in captures]

    assert found_templates == [text]

    assert_captures_in_text(captures, text)


def test_multiline_template():
    text = dedent('''\
        {{cite journal
        | vauthors = Poland GA, Jacobson RM
        | title = The Age-Old Struggle against the Antivaccinationists
        | journal = N Engl J Med
        | volume = 364
        | pages = 97–9
        | date = 13 January 2011
        | pmid = 21226573
        | doi = 10.1056/NEJMp1010594
        | url = http://www.nejm.org/doi/full/10.1056/NEJMp1010594
        | archiveurl = http://web.archive.org/web/20140423082318/http://www.nejm.org/doi/full/10.1056/NEJMp1010594
        | archivedate = 23 April 2014 }}''')
    captures = list(templates(text))

    found_templates = [capture.data for capture in captures]

    assert found_templates == [text]

    assert_captures_in_text(captures, text)


def test_fucked_up_template():
    # As bad as it could be
    text = dedent('''\
        {{


                        cite journal
        |
        vauthors = Poland GA, Jacobson RM |
        title = The Age-Old Struggle


        against the Antivaccinationists | journal
        = N Engl J Med | volume = 364 | pages = 97–9 | date = 13
        January 2011 | pmid = 21226573 | doi = 10.1056/NEJMp1010594 | url = http://www.nejm.org/doi/full/10.1056/NEJMp1010594 |
                                     archiveurl = http://web.archive.org/web/20140423082318/http://www.nejm.org/doi/full/10.1056/NEJMp1010594 | archivedate = 23 April 2014 }}''')

    captures = list(templates(text))

    found_templates = [capture.data for capture in captures]

    assert found_templates == [text]

    assert_captures_in_text(captures, text)
