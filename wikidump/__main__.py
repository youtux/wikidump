import argparse
import collections
import sys
import subprocess
import codecs

import mw.xml_dump
import mwxml
import pathlib
import regex

from . import dumper, extractors, utils, languages, mwcites_extractors

Citation = collections.namedtuple("Citation", "type id")

Page = collections.namedtuple("Page", "id title namespace revisions")
Revision = collections.namedtuple("Revision",
    "id timestamp references_diff sections bibliography")
Revision.Section = collections.namedtuple('Section', "name level")
Revision.ReferenceDiff = collections.namedtuple("ReferenceDiff", "action text")
# IdentifierStats = collections.namedtuple("IdentifierStats",
#     "type id appearances")
# Appearance = collections.namedtuple("Appearance",
#     "raw in_tag_ref in_template_citation in_tag_ref_and_template_citation")


def DefaultStatsDict():
    return {
        'raw': 0,
        'in_tag_ref': 0,
        'in_template_citation': 0,
        'in_tag_ref_and_template_citation': 0,
    }

global_stats = {
    'identifiers': {},
}


def dot(num=None):
    if not num:
        what = '.'
    elif num < 10:
        what = str(num)
    else:
        what = '>'
    print(what, end='', file=sys.stderr, flush=True)


def log(*args):
    first, *rest = args
    print('\n' + str(first), *rest, end='', file=sys.stderr, flush=True)


def remove_comments(source):
    pattern = regex.compile(r'<!--(.*?)-->', regex.MULTILINE | regex.DOTALL)
    return pattern.sub('', source)


def revisions_extractor(revisions, language):
    prev_references = set()
    for mw_revision in revisions:
        dot()
        text = remove_comments(mw_revision.text or '')
        references = extractors.references(text)
        sections = extractors.sections(text)
        bibliography = "".join(extractors.bibliography(text, language))
        citations = extractors.citation(text, language)
        dois = list(mwcites_extractors.doi.extract(text))

        for doi in dois:
            in_tag_ref = any(doi.id in ref for ref in references)
            in_template_citation = any(doi.id in c for c in citations)

            # appearance = Appearance(
            #     raw=not in_tag_ref and not in_template_citation,
            #     in_tag_ref=in_tag_ref,
            #     in_template_citation=in_template_citation,
            # )
            doi_stats = global_stats['identifiers'].setdefault(
                doi, DefaultStatsDict())
            if not in_tag_ref and not in_template_citation:
                doi_stats['raw'] += 1
            if in_tag_ref and not in_template_citation:
                doi_stats['in_tag_ref'] += 1
            if in_template_citation and not in_tag_ref:
                doi_stats['in_template_citation'] += 1
            if in_tag_ref and in_template_citation:
                doi_stats['in_tag_ref_and_template_citation'] += 1

        yield Revision(
            id=mw_revision.id,
            timestamp=mw_revision.timestamp.to_json(),
            references_diff=references_diff(prev_references, references),
            sections=sections,
            bibliography=bibliography,
        )

        prev_references = references


def references_diff(prev_references, references):
    # prev_references = [ref.text for ref in prev_references]
    # references = [ref.text for ref in references]

    added = set(references) - set(prev_references)
    removed = set(prev_references) - set(references)

    references_diffs = (
        [Revision.ReferenceDiff('added', ref) for ref in added]
        + [Revision.ReferenceDiff('removed', ref) for ref in removed]
    )

    return references_diffs


def page_extractor(dump, language):
    for mw_page in dump:
        log("Processing", mw_page)

        yield Page(
            id=mw_page.id,
            title=mw_page.title,
            namespace=mw_page.namespace,
            revisions=revisions_extractor(mw_page, language=language),
        )


def open_xml_file(path):
    f = mw.xml_dump.functions.open_file(
        mw.xml_dump.functions.file(path)
    )
    return f


def compressor_7z(file_path):
    p = subprocess.Popen(
        ['7z', 'a', '-si', file_path],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    utf8writer = codecs.getwriter('utf-8')

    return utf8writer(p.stdin)


def output_writer(path, compression):
    if compression == '7z':
        return compressor_7z(path)
    else:
        return open(path, 'wt', encoding='utf-8')


def create_path(path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)


def get_args():
    parser = argparse.ArgumentParser(
        prog='wikidump',
        description='Wikidump features extractor.',
    )
    parser.add_argument('files',
        metavar='FILE',
        type=pathlib.Path,
        nargs='+',
        help='XML Wikidump file to parse. It accepts only 7z.'
    )
    parser.add_argument('output_dir_path',
        metavar='OUTPUT_DIR',
        type=pathlib.Path,
        help='XML output directory.',
    )
    parser.add_argument('-l', '--language',
        choices=languages.supported,
        required=True,
        help='The language of the dump.',
    )
    parser.add_argument('--output-compression',
        choices={None, '7z'},
        required=False,
        default=None,
        help='Output compression format.',
    )

    return parser.parse_args()


def main():
    args = get_args()

    args.output_dir_path.mkdir(parents=True, exist_ok=True)

    for input_file_path in args.files:
        log("Analyzing {}...".format(input_file_path))
        dump = mwxml.Dump.from_file(open_xml_file(str(input_file_path)))

        basename = input_file_path.name

        with output_writer(str(args.output_dir_path/basename),
                           compression=args.output_compression) as out:
            dumper.serialize(
                pages=page_extractor(dump, language=args.language),
                stats=global_stats,
                output_handler=out,
            )


if __name__ == '__main__':
    main()
