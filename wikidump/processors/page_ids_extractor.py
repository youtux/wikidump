"""Extract all the page ids to a csv file."""

import csv

import mwxml

from .. import utils


def configure_subparsers(subparsers):
    """Configure the subparsers."""
    parser = subparsers.add_parser(
        'extract-page-ids',
        help='''Extract the page ids from the text.''',
    )

    parser.set_defaults(func=main)


def main(dump: mwxml.Dump,
         features_output_h,
         stats_output_h,
         args):
    """Main function that parses the arguments and writes the output."""
    print(args)

    with features_output_h:
        csvwriter = csv.writer(features_output_h)

        for mw_page in dump:
            utils.log('Analyzing', mw_page.title)
            csvwriter.writerow((mw_page.id, mw_page.title))
