import ipdb
"""Extract all the identifiers (doi, pubmed, isbn, arxiv).

Also, keep a stats file that counts where the identifiers have been found."""
import collections
import datetime
import functools
import itertools
import sys

import more_itertools
import mwxml
from typing import Iterable, Mapping, Callable
import networkx

from .. import dumper, extractors, utils


stats_template = '''
<stats>
    <performance>
        <start_time>${stats['performance']['start_time']}</start_time>
        <end_time>${stats['performance']['end_time']}</end_time>
        <revisions_analyzed>${stats['performance']['revisions_analyzed']}</revisions_analyzed>
        <pages_analyzed>${stats['performance']['pages_analyzed']}</pages_analyzed>
    </performance>
    <identifiers>
        % for key in ['global', 'last_revision']:
        <${key}>
            % for where, count in stats['identifiers'][key].items():
            <appearance where="${where}" count="${count}" />
            % endfor
        </${key}>
        % endfor
    </identifiers>
</stats>
'''

Page = collections.namedtuple('Page', [
    'id',
    'title',
    'revisions',
])
Revision = collections.namedtuple('Revision', [
    'id',
    'user',
    'timestamp',
    'publication_identifiers_diff',
])


def add_appearance(
        appearances_dict,
        identifier,
        page_id,
        page_title,
        revision_id,
        revision_timestamp,
        ):
    appearance = appearances_dict.setdefault(
        identifier,
        {
            'pages': dict(),
        },
    )
    page = appearance['pages'].setdefault(
        page_id,
        {
            'page_title': page_title,
            'revisions': dict()
        },
    )
    page['revisions'][revision_id] = revision_timestamp


def always_true(*args, **kwargs) -> bool:
    """Return True."""
    return True


def extract_revisions(
        page: mwxml.Page,
        stats: Mapping,
        only_last_revision: bool,
        section_filter: Callable[[extractors.misc.Section], bool]=always_true,
        ) -> Iterable[Revision]:
    """Extract the identifiers from the revisions."""
    revisions = more_itertools.peekable(page)

    stats_identifiers = stats['identifiers']

    prev_identifiers = set()
    for mw_revision in revisions:
        utils.dot()

        is_last_revision = not utils.has_next(revisions)
        if only_last_revision and not is_last_revision:
            continue

        text = utils.remove_comments(mw_revision.text or '')

        identifiers_captures = list(extractors.pub_identifiers(text))
        identifiers = [identifier for identifier, _ in identifiers_captures]


        yield Revision(
            id=mw_revision.id,
            user=mw_revision.user,
            timestamp=mw_revision.timestamp.to_json(),
            publication_identifiers_diff=utils.diff(prev_identifiers,
                                                    identifiers_filtered),
        )

        stats['performance']['revisions_analyzed'] += 1
        prev_identifiers = identifiers_filtered


def extract_pages(
        dump: mwxml.Dump,
        stats: Mapping,
        only_last_revision: bool,  # TODO: default value to False
        section_filter: Callable[[extractors.misc.Section], bool]=always_true,
        ) -> Iterable[Page]:
    """"Extract the pages from the dump."""
    for mw_page in dump:
        utils.log("Processing", mw_page.title)

        # Skip non-articles
        if mw_page.namespace != 0:
            utils.log('Skipped (namespace != 0)')
            continue

        revisions_generator = extract_revisions(
            mw_page,
            stats=stats,
            only_last_revision=only_last_revision,
            section_filter=section_filter,
        )

        yield Page(
            id=mw_page.id,
            title=mw_page.title,
            revisions=revisions_generator,
        )
        stats['performance']['pages_analyzed'] += 1


def configure_subparsers(subparsers):
    """Configure the subparsers."""
    parser = subparsers.add_parser(
        'extract-identifiers-stats',
        help='''Extract the identifiers from the text (doi, isbn, arxiv and \
pubmed).''',
    )
    parser.add_argument(
        '--only-last-revision',
        action='store_true',
        help='Consider only the last revision for each page.',
    )
    parser.set_defaults(func=main)

def identifiers_in_revision(mw_revision):
    utils.dot()
    text = utils.remove_comments(mw_revision.text or '')
    identifiers = [
        # extractors.common.Identifier(sys.intern(identifier.type), sys.intern(identifier.id))
        identifier
        for identifier, _ in extractors.pub_identifiers(text)
    ]
    return identifiers


def mw_timestamp_to_datetime(ts):
    timestamp = datetime.datetime.fromtimestamp(
        ts.unix(),
        datetime.timezone.utc,
    )
    return timestamp

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def revisions_topology(revisions):
    topology = networkx.DiGraph()
    for revision in revisions:
        timestamp = datetime.datetime.fromtimestamp(
            revision.timestamp.unix(),
            datetime.timezone.utc,
        )
        # if timestamp < datetime.datetime(2007,12,1, tzinfo=datetime.timezone.utc):
        #     continue
        # Much RAM is used. Maybe use some mechanism of string intern?
        topology.add_node(
            revision.id,
            timestamp=timestamp,
            # identifiers=identifiers_in_revision(revision),
        )
        topology.add_edge(revision.parent_id, revision.id)

    return topology

    # history_by_topological_sort = [
    #     (revision_id, topology.node[revision_id]['timestamp'],  topology.node[revision_id]['identifiers'])
    #     for revision_id in networkx.topological_sort(topology)
    #     if revision_id is not None
    # ]

def main(dump: mwxml.Dump,
         features_output_h,
         stats_output_h,
         args):
    """Main function that parses the arguments and writes the output."""
    stats = {
        'performance': {
            'start_time': None,
            'end_time': None,
            'revisions_analyzed': 0,
            'pages_analyzed': 0,
        },
    }
    print(args)
    only_last_revision = args.only_last_revision

    import sqlite3
    import enum

    class Action(enum.Enum):
        added = 1
        removed = 2

    conn = sqlite3.connect('identifiers.db')
    c = conn.cursor()
    # TODO: Add the project type (en, it, ...)
    c.executescript('''

-- Table: identifiers_history
CREATE TABLE IF NOT EXISTS identifiers_history (identifier TEXT NOT NULL, "action" INTEGER NOT NULL, timestamp DATETIME NOT NULL, page_id INTEGER NOT NULL, revision_id INTEGER NOT NULL, PRIMARY KEY (identifier, "action", timestamp, page_id, revision_id));

-- Index: timestamp_asc
CREATE INDEX IF NOT EXISTS timestamp_asc ON identifiers_history (timestamp ASC);

-- Index: identifier_asc
CREATE INDEX IF NOT EXISTS identifier_asc ON identifiers_history (identifier ASC);

-- Index: page_revision_asc
CREATE INDEX IF NOT EXISTS page_revision_asc ON identifiers_history (page_id ASC, revision_id ASC);

    ''')

    for mw_page in dump:
        utils.log('Analyzing ', mw_page.title)

        revisions = more_itertools.peekable(mw_page)

        if only_last_revision:
            for revision in revisions:
                if utils.has_next(revisions):
                    continue
                revisions = [revision]

        history = [
            (
                revision.id,
                mw_timestamp_to_datetime(revision.timestamp),
                identifiers_in_revision(revision),
            )
            for revision in revisions
        ]

        history.sort(key=lambda r: r[1])

        diff_history = []

        history_with_empty_first = itertools.chain(
            [(history[0][0], history[0][1], [])],
            history,
        )

        for pair in pairwise(history_with_empty_first):
            pair_identifiers = [el[2] for el in pair]
            diff = utils.diff(*pair_identifiers)
            val = (pair[1][0], pair[1][1], diff)
            diff_history.append(val)

        # import pickle
        # pickle.dump(diff_history, 'autism-history')

        identifiers_history = []
        for rev_id, timestamp, diffs in diff_history:
            for action, identifier in diffs:
                identifiers_history.append((
                    identifier.type + "_" + identifier.id,
                    action,
                    timestamp,
                    mw_page.id,
                    rev_id
                ))

        c.executemany(
            'INSERT INTO identifiers_history VALUES (?,?,?,?,?)',
            identifiers_history,
        )

        print("commit...")
        conn.commit()

    c.close()



    # with features_output_h:
    #     stats['performance']['start_time'] = datetime.datetime.utcnow()
    #     dumper.render_template(
    #         features_template,
    #         output_handler=features_output_h,
    #         pages=pages_generator,
    #     )
    #     stats['performance']['end_time'] = datetime.datetime.utcnow()
    #
    # with stats_output_h:
    #     dumper.render_template(
    #         stats_template,
    #         stats_output_h,
    #         stats=stats,
    #     )
