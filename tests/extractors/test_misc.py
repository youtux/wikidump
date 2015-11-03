from wikidump.extractors.misc import Section, sections, templates, references

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


def test_references_with_quotes_and_double_quotes():
    text = dedent('''\
        <ref foo="bar" bar='foo' foobar='foo"b"ar'>test1</ref>''')
    captures = list(references(text))
    found_templates = [capture.data for capture in captures]

    assert found_templates == [text]
    assert_captures_in_text(captures, text)


def test_references_with_attributes():
    text = dedent('''\
        <ref foo="bar" bar="foo" >test1</ref>''')
    captures = list(references(text))
    found_templates = [capture.data for capture in captures]

    assert found_templates == [text]
    assert_captures_in_text(captures, text)


def test_multiple_references():
    text = dedent('''\
        <ref>test1</ref>
        <ref>test2</ref>
        ''')
    captures = list(references(text))
    found_templates = [capture.data for capture in captures]

    assert found_templates == ['<ref>test1</ref>', '<ref>test2</ref>']
    assert_captures_in_text(captures, text)


def test_multiline_reference():
    text = dedent('''\
        <ref name="vaccines">Vaccines and autism:
        * {{cite journal | vauthors = Doja A, Roberts W | title = Immunizations and autism: a review of the literature | journal = [[Can J Neurol Sci]] | volume = 33 | issue = 4 | pages = 341–6 | year = 2006 | pmid = 17168158 | doi=10.1017/s031716710000528x}}
        * {{cite journal | vauthors = Gerber JS, Offit PA | title = Vaccines and autism: a tale of shifting hypotheses | journal = [[Clin Infect Dis]] | volume = 48 | issue = 4 | pages = 456–61 | year = 2009 | pmid = 19128068 | pmc = 2908388 | doi = 10.1086/596476 | url = http://cid.oxfordjournals.org/content/48/4/456.full | archiveurl = http://web.archive.org/web/20131031043545/http://cid.oxfordjournals.org:80/content/48/4/456.full | archivedate = 31 October 2013 }}
        * {{cite journal | vauthors = Gross L | title = A broken trust: lessons from the vaccine–autism wars | journal = PLoS Biol | volume = 7 | issue = 5 | pages = e1000114 | year = 2009 | pmid = 19478850 | pmc = 2682483 | doi = 10.1371/journal.pbio.1000114 }}
        * {{cite journal | vauthors = Paul R | title = Parents ask: am I risking autism if I vaccinate my children? | journal = [[J Autism Dev Disord]] | volume = 39 | issue = 6 | pages = 962–3 | year = 2009 | pmid = 19363650 | doi = 10.1007/s10803-009-0739-y }}
        * {{cite journal | vauthors = Poland GA, Jacobson RM | title = The Age-Old Struggle against the Antivaccinationists | journal = N Engl J Med | volume = 364 | pages = 97–9 | date = 13 January 2011 | pmid = 21226573 | doi = 10.1056/NEJMp1010594 | url = http://www.nejm.org/doi/full/10.1056/NEJMp1010594 | archiveurl = http://web.archive.org/web/20140423082318/http://www.nejm.org/doi/full/10.1056/NEJMp1010594 | archivedate = 23 April 2014 }}</ref>''')
    captures = list(references(text))
    found_templates = [capture.data for capture in captures]
    assert found_templates == [text]
    assert_captures_in_text(captures, text)
