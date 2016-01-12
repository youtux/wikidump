"""Extract identifiers history.

The output format is csv.

The program analyze one page at a time, and it outputs the history of the
identifier of the page.
"""
import collections
import csv
import datetime
import itertools

import more_itertools
import mwxml
import networkx

from .. import extractors, utils

PageHistoryElem = collections.namedtuple(
    'PageHistoryElem',
    'identifier revision_id timestamp action',
)

Revision = collections.namedtuple(
    'Revision',
    'id timestamp identifiers',
)


def configure_subparsers(subparsers):
    """Configure the subparsers."""
    parser = subparsers.add_parser(
        'extract-identifiers-history',
        help='''Extract the identifiers from the text (doi, isbn, arxiv and \
pubmed).''',
    )
    parser.add_argument(
        '--project', '-p',
        required=True,
        help='Wikimedia project.',
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
    print(args)

    writer = csv.writer(features_output_h)

    for mw_page in dump:
        utils.log('Analyzing ', mw_page.title)

        if mw_page.namespace != 0:
            utils.log('Skipped (namespace != 0)')
            continue

        revisions = more_itertools.peekable(mw_page)

        history = [
            Revision(
                revision.id,
                revision.timestamp,
                identifiers_in_revision(revision),
            )
            for revision in revisions
        ]

        history.sort(key=lambda r: (r.timestamp, r.id))

        first_rev = history[0]
        history_with_empty_first = itertools.chain(
            [Revision(first_rev.id, first_rev.timestamp, [])],
            history,
        )

        diff_history = [
            (r2.id, r2.timestamp, utils.diff(r1.identifiers, r2.identifiers))
            for r1, r2 in utils.pairwise(history_with_empty_first)
        ]

        page_history = [
            PageHistoryElem(identifier, revision_id, timestamp, action)
            for revision_id, timestamp, diffs in diff_history
            for action, identifier in diffs
        ]

        page_history.sort(
            key=lambda r: (r.identifier, r.timestamp, r.revision_id)
        )

        lastvalue = PageHistoryElem(
            identifier=None,
            timestamp=None,
            revision_id=None,
            action='removed',
        )

        page_history_by_identifier = itertools.groupby(
            page_history,
            key=lambda r: (r.identifier),
        )

        for identifier, actions in page_history_by_identifier:
            for r1, r2 in utils.grouper(actions, 2, fillvalue=lastvalue):
                assert r1.action != r2.action
                assert r2.timestamp is None or r1.timestamp <= r2.timestamp

                writer.writerow((
                    args.project,
                    mw_page.id,
                    mw_page.title,
                    identifier.type,
                    identifier.id,
                    r1.timestamp,
                    r2.timestamp,
                ))

    features_output_h.close()
