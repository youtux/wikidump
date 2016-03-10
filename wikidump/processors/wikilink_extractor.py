"""Extract wikilinks from pages.

The output format is csv.
"""

import csv
import collections
import datetime
import functools

import fuzzywuzzy.process
import jsonable
import more_itertools
import mwxml
from typing import Iterable, Iterator, Mapping, NamedTuple, Optional

from .. import dumper, extractors, languages, utils

Revision = NamedTuple('Revision', [
    ('id', int),
    ('parent_id', int),
    ('user', Optional[mwxml.Revision.User]),
    ('minor', bool),
    ('comment', str),
    ('model', str),
    ('format', str),
    ('timestamp', jsonable.Type),
    ('text', str),
    ('wikilinks', Iterable[extractors.misc.Wikilink])
])


Page = NamedTuple('Page', [
    ('id', str),
    ('namespace', int),
    ('title', str),
    ('revisions', Iterable[Revision]),
])


def extract_revisions(
        mw_page: mwxml.Page,
        language: str,
        stats: Mapping,
        only_last_revision: bool) -> Iterator[Revision]:
    """Extract the internall links (wikilinks) from the revisions."""

    revisions = more_itertools.peekable(mw_page)
    for mw_revision in revisions:
        utils.dot()

        is_last_revision = not utils.has_next(revisions)
        if only_last_revision and not is_last_revision:
            continue

        text = utils.remove_comments(mw_revision.text or '')

        wikilinks = (wikilink
                     for wikilink, _
                     in extractors.wikilinks(text, extractors.sections(text)))

        yield Revision(
            id=mw_revision.id,
            parent_id=mw_revision.parent_id,
            user=mw_revision.user,
            minor=mw_revision.minor,
            comment=mw_revision.comment,
            model=mw_revision.model,
            format=mw_revision.format,
            timestamp=mw_revision.timestamp.to_json(),
            text=text,
            wikilinks=wikilinks
        )


def extract_pages(
        dump: Iterable[mwxml.Page],
        language: str,
        stats: Mapping,
        only_last_revision: bool) -> Iterator[Page]:
    """Extract revisions from a page."""
    for mw_page in dump:
        utils.log("Processing", mw_page.title)

        # Skip non-articles
        if mw_page.namespace != 0:
            utils.log('Skipped (namespace != 0)')
            continue

        revisions_generator = extract_revisions(
            mw_page,
            language=language,
            stats=stats,
            only_last_revision=only_last_revision,
        )

        yield Page(
            id=mw_page.id,
            namespace=mw_page.namespace,
            title=mw_page.title,
            revisions=revisions_generator,
        )


def configure_subparsers(subparsers):
    """Configure a new subparser."""
    parser = subparsers.add_parser(
        'extract-wikilinks',
        help='Extract internal links (wikilinks)',
    )
    parser.add_argument(
        '-l', '--language',
        choices=languages.supported,
        required=True,
        help='The language of the dump.',
    )
    parser.add_argument(
        '--only-last-revision',
        action='store_true',
        help='Consider only the last revision for each page.',
    )
    parser.set_defaults(func=main)


def main(
        dump: Iterable[mwxml.Page],
        features_output_h,
        stats_output_h,
        args) -> None:
    """Main function that parses the arguments and writes the output."""
    stats = {
        'performance': {
            'start_time': None,
            'end_time': None,
            'revisions_analyzed': 0,
            'pages_analyzed': 0,
        },
        'section_names': {
            'global': collections.Counter(),
            'last_revision': collections.Counter(),
        },
    }

    writer = csv.writer(features_output_h)

    pages_generator = extract_pages(
        dump,
        language=args.language,
        stats=stats,
        only_last_revision=args.only_last_revision,
    )

    writer.writerow((
        'page_id',
        'page_title',
        'revision_id',
        'revision_parent_id',
        'revision_timestamp'
        'user_type',
        'user_username',
        'user_id',
        'revision_minor',
        'wikilink.link',
        'wikilink.anchor',
        'wikilink.section_name',
        'wikilink.section_level',
        'wikilink.section_number'
        ))

    for mw_page in pages_generator:
        for revision in mw_page.revisions:

            if revision.user is None:
                user_type = 'None'
                user_username = 'None'
                user_id = -2
            else:
                if revision.user.id is not None:
                    user_type = 'registered'
                    user_username = revision.user.text
                    user_id = revision.user.id
                else:
                    user_type = 'ip'
                    user_username = revision.user.text
                    user_id = -1

            revision_parent_id = revision.parent_id
            if revision.parent_id is None:
                revision_parent_id = -1

            if revision.minor:
                revision_minor = 1
            else:
                revision_minor = 0

            for wikilink in revision.wikilinks:
                # project,page.id,page.title,revision.id,revision.parent_id,
                # revision.timestamp,contributor_if_exists(revision.user),
                # revision.minor,wikilink.link,wikilink.anchor,
                # wikilink.section_name,wikilink.section_level,
                # wikilink.section_number
                writer.writerow((
                    mw_page.id,
                    mw_page.title,
                    revision.id,
                    revision.parent_id,
                    revision.timestamp,
                    user_type,
                    user_username,
                    user_id,
                    revision_minor,
                    wikilink.link,
                    wikilink.anchor,
                    wikilink.section_name,
                    wikilink.section_level,
                    wikilink.section_number
                ))
