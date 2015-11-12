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
import more_itertools

from . import dumper, utils, extractors, languages

Citation = collections.namedtuple("Citation", "type id")

Page = collections.namedtuple("Page", "id title namespace revisions")
Revision = collections.namedtuple("Revision",
    '''id user timestamp references_diff publication_identifiers_diff sections
    bibliography''')
Revision.Section = collections.namedtuple('Section', "name level")
Diff = collections.namedtuple("Diff", "action data")

# IdentifierStats = collections.namedtuple("IdentifierStats",
#     "type id appearances")
# Appearance = collections.namedtuple("Appearance",
#     "raw in_tag_ref in_template_citation in_tag_ref_and_template_citation")


def IdentifierStatsDict():
    return {
        'only_in_raw_text': 0,
        'only_in_tag_ref': 0,
        'only_in_template': 0,
        'in_tag_ref_and_template': 0,
    }


def GlobalStatsDict():
    return {
        'sections_per_revision': {
            'global': collections.Counter(),
            'last_revision': collections.Counter(),
        },
        'section_names_per_revision': {
            'global': collections.Counter(),
            'last_revision': collections.Counter(),
        },
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


def has_next(peekable):
    try:
        peekable.peek()
        return True
    except StopIteration:
        return False


@utils.listify(wrapper=set)
def where_appears(span, **spans):
    span_le = extractors.Span.__le__
    for key, span_list in spans.items():
        # if any(span <= other_span) for other_span in span_list):
        # HACK: the following is more efficient. Sorry :(
        if any(span_le(span, other_span) for other_span in span_list):
            yield key


def identifier_appearance_stat_key(appearances):
    if {'templates', 'references'} <= appearances:
        return 'in_tag_ref_and_template'
    elif 'templates' in appearances:
        return 'only_in_template'
    elif 'references' in appearances:
        return 'only_in_tag_ref'
    else:
        return 'only_in_raw_text'


def revisions_extractor(revisions, language, stats):
    section_names_stats = stats['section_names_per_revision']
    sections_stats = stats['sections_per_revision']
    revisions = more_itertools.peekable(revisions)
    for mw_revision in revisions:
        dot()

        is_last_revision = not has_next(revisions)

        text = remove_comments(mw_revision.text or '')

        section_names = [section.name.strip().lower()
                         for section, _ in extractors.sections(text)]
        sections_count = len(section_names)

        for section_name in section_names:
            section_names_stats['global'][section_name] += 1
            if is_last_revision:
                section_names_stats['last_revision'][section_name] += 1

        sections_stats['global'][sections_count] += 1
        if is_last_revision:
            sections_stats['last_revision'][sections_count] += 1

        yield None

        stats['performance']['revisions_analyzed'] += 1


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

        # Skip non-articles
        if mw_page.namespace != 0:
            continue

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
            stats_output = open(os.devnull, 'wt')
        else:
            stats_output = output_writer(
                path=str(args.output_dir_path/(basename + '.stats.xml')),
                compression=args.output_compression,
            )

        stats['performance']['start_time'] = datetime.datetime.utcnow()

        # Process the stats
        for page in page_extractor(dump,
                language=args.language,
                stats=stats,
                ):
            for revision in page.revisions:
                pass

        stats['performance']['end_time'] = datetime.datetime.utcnow()

        with stats_output:
            dumper.serialize_stats(stats, stats_output)


if __name__ == '__main__':
    main()
