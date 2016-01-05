import ipdb
"""Extract all the identifiers (doi, pubmed, isbn, arxiv).

Also, keep a stats file that counts where the identifiers have been found."""
import collections
import datetime
import functools
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

    for mw_page in dump:
        revisions = more_itertools.peekable(mw_page)

        if only_last_revision:
            for revision in revisions:
                if utils.has_next(revisions):
                    continue
                revisions = [revision]

        topology = networkx.DiGraph()
        for revision in revisions:
            timestamp = datetime.datetime.fromtimestamp(
                revision.timestamp.unix(),
                datetime.timezone.utc,
            )
            # Much RAM is used. Maybe use some mechanism of string intern?
            topology.add_node(
                revision.id,
                # timestamp=timestamp,
                # identifiers=identifiers_in_revision(revision),
            )
            topology.add_edge(revision.parent_id, revision.id)

        if not networkx.is_weakly_connected(topology):
            ipdb.set_trace()  ######### Break Point ###########

        assert networkx.is_weakly_connected(topology)


        # history = [
        #     (revision_id, topology.node[revision_id]['timestamp'],  topology.node[revision_id]['identifiers'])
        #     for revision_id in networkx.topological_sort(topology)
        #     if revision_id is not None
        # ]



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
