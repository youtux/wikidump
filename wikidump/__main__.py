import argparse
import collections
import sys
import subprocess
import codecs

import mw.xml_dump
import mwxml
import pathlib
import regex

from . import dumper, extractors, utils

Citation = collections.namedtuple("Citation", "type id")

Page = collections.namedtuple("Page", "id title namespace revisions")
Revision = collections.namedtuple("Revision",
    "id timestamp references_diff sections bibliography")
Revision.Section = collections.namedtuple('Section', "name level")
Revision.ReferenceDiff = collections.namedtuple("ReferenceDiff", "action text")


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
    pattern = regex.compile(r'<!--(.*?)-->', regex.MULTILINE)
    return pattern.sub('', source)


def revisions_extractor(revisions):
    prev_references = set()
    for revision in revisions:
        dot()
        text = remove_comments(revision.text or '')
        references = extractors.references(text)
        sections = extractors.sections(text)
        bibliography = "".join(extractors.bibliography(text))

        yield Revision(
            id=revision.id,
            timestamp=revision.timestamp.to_json(),
            references_diff=references_diff(prev_references, references),
            sections=sections,
            bibliography=bibliography,
        )

        prev_references = references


def references_diff(prev_references, references):
    # prev_references = [ref.text for ref in prev_references]
    # references = [ref.text for ref in references]

    added_references = set(references) - set(prev_references)
    removed_references = set(prev_references) - set(references)

    references_diffs = (
        [Revision.ReferenceDiff('added', ref.text) for ref in added_references]
        + [Revision.ReferenceDiff('removed', ref.text) for ref in removed_references]
    )

    return references_diffs


def page_extractor(dump):
    for page in dump:
        log("Processing", page)

        my_page = Page(
            id=page.id,
            title=page.title,
            namespace=page.namespace,
            revisions=revisions_extractor(page),
        )

        yield my_page


def open_xml_file(path):
    f = mw.xml_dump.functions.open_file(
        mw.xml_dump.functions.file(path)
    )
    return f


def compressor_7z(file_path, *args, **kwargs):
    p = subprocess.Popen(
        ['7z', 'a', '-si', file_path],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    utf8writer = codecs.getwriter('utf-8')

    return utf8writer(p.stdin)


def create_path(path):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description='Wikidump extractor.')
    parser.add_argument('files', metavar='FILE', type=pathlib.Path, nargs='+',
                        help='XML Wikidump file to parse')
    parser.add_argument('output_dir_path', metavar='OUTPUT_DIR',
                        type=pathlib.Path, help='XML output directory')

    args = parser.parse_args()

    args.output_dir_path.mkdir(parents=True, exist_ok=True)

    for input_file_path in args.files:
        log("Analyzing {}...".format(input_file_path))
        dump = mwxml.Dump.from_file(open_xml_file(str(input_file_path)))

        basename = input_file_path.name

        with compressor_7z(str(args.output_dir_path/basename), 'wt', encoding='utf-8') as out:
            dumper.serialize(page_extractor(dump), out)


if __name__ == '__main__':
    main()
