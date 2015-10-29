import argparse
import collections
import sys
import subprocess
import codecs
import os
import datetime

import mw.xml_dump
import mwxml
import pathlib
import regex

from . import dumper, extractors, languages

Citation = collections.namedtuple("Citation", "type id")

Page = collections.namedtuple("Page", "id title namespace revisions")
Revision = collections.namedtuple("Revision",
    '''id timestamp references_diff publication_identifiers_diff sections
    bibliography''')
Revision.Section = collections.namedtuple('Section', "name level")
Diff = collections.namedtuple("Diff", "action data")
# IdentifierStats = collections.namedtuple("IdentifierStats",
#     "type id appearances")
# Appearance = collections.namedtuple("Appearance",
#     "raw in_tag_ref in_template_citation in_tag_ref_and_template_citation")


def IdentifierStatsDict():
    return {
        'raw': 0,
        'in_tag_ref': 0,
        'in_template': 0,
        'in_tag_ref_and_template': 0,
    }


def GlobalStatsDict():
    return {
        'identifiers': {},
        'performance': {
            'start_time': None,
            'end_time': None,
            'revisions_analyzed': 0,
            'pages_analyzed': 0,
        }
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


def revisions_extractor(revisions, language, stats):
    prev_references = set()
    prev_pub_identifiers = set()
    for mw_revision in revisions:
        dot()
        text = remove_comments(mw_revision.text or '')
        references = extractors.references(text)
        sections = extractors.sections(text)
        bibliography = "".join(extractors.bibliography(text, language))
        templates = extractors.templates(text)
        pub_identifiers = extractors.pub_identifiers(text)

        for pub_identifier in pub_identifiers:
            # TODO: improve the performance of these searches:
            # it's much faster to use
            #   pub_identifier.id in "".join(references)
            # but less readable and more vulnerable
            in_tag_ref = any(pub_identifier.id in ref for ref in references)
            in_template = any(pub_identifier.id in t for t in templates)

            identifier_stats = stats['identifiers'].setdefault(
                pub_identifier, IdentifierStatsDict())
            if not in_tag_ref and not in_template:
                identifier_stats['raw'] += 1
            if in_tag_ref and not in_template:
                identifier_stats['in_tag_ref'] += 1
            if in_template and not in_tag_ref:
                identifier_stats['in_template'] += 1
            if in_tag_ref and in_template:
                identifier_stats['in_tag_ref_and_template'] += 1

        yield Revision(
            id=mw_revision.id,
            timestamp=mw_revision.timestamp.to_json(),
            references_diff=diff(prev_references, references),
            publication_identifiers_diff=diff(prev_pub_identifiers,
                pub_identifiers),
            sections=sections,
            bibliography=bibliography,
        )

        stats['performance']['revisions_analyzed'] += 1
        prev_references = references
        prev_pub_identifiers = pub_identifiers


def diff(previous, current):
    # previous = [ref.text for ref in previous]
    # current = [ref.text for ref in current]

    added = set(current) - set(previous)
    removed = set(previous) - set(current)

    diff = (
        [Diff('added', el) for el in added]
        + [Diff('removed', el) for el in removed]
    )

    return diff


def page_extractor(dump, language, stats):
    for mw_page in dump:
        log("Processing", mw_page)

        yield Page(
            id=mw_page.id,
            title=mw_page.title,
            namespace=mw_page.namespace,
            revisions=revisions_extractor(
                mw_page,
                language=language,
                stats=stats,
            ),
        )
        stats['performance']['pages_analyzed'] += 1


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
        return compressor_7z(path + '.7z')
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
    parser.add_argument('--dry-run', '-n',
        action='store_true',
        help="Don't write any file",
    )

    return parser.parse_args()


def main():
    args = get_args()

    args.output_dir_path.mkdir(parents=True, exist_ok=True)

    for input_file_path in args.files:
        log("Analyzing {}...".format(input_file_path))

        stats = GlobalStatsDict()
        dump = mwxml.Dump.from_file(open_xml_file(str(input_file_path)))

        basename = input_file_path.name

        if args.dry_run:
            pages_output = open(os.devnull, 'wt')
            stats_output = open(os.devnull, 'wt')
        else:
            pages_output = output_writer(
                path=str(args.output_dir_path/(basename + '.features.xml')),
                compression=args.output_compression,
            )
            stats_output = output_writer(
                path=str(args.output_dir_path/(basename + '.stats.xml')),
                compression=args.output_compression,
            )

        stats['performance']['start_time'] = datetime.datetime.utcnow()
        with pages_output:
            dumper.serialize_page_revisions(
                pages=page_extractor(dump,
                    language=args.language,
                    stats=stats,
                ),
                output_handler=pages_output,
            )
        stats['performance']['end_time'] = datetime.datetime.utcnow()

        with stats_output:
            dumper.serialize_stats(stats, stats_output)


if __name__ == '__main__':
    main()
