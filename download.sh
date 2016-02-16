#!/usr/bin/env bash

eval "$(docopts -V - -h - : "$@" <<EOF
Usage: download.sh [-f FILTER] [-l LIST] [-n] [-o OUTDIR] [-v] -d DATE PROJECT
       download.sh [-v] --md5-only -d DATE PROJECT
       download.sh (-h | --help)

      -d, --date DATE           Dump date (format: yyyymmdd).
      -f, --filter FILTER       Filter files names to download (defult: 'history').
      -l, --list LIST           List of files to download (default: download MD5 file).
                                (implies --md5-no-download)
      --md5-only                Only download the MD5 sums file.
      -n, --md5-no-download     Do not download the MD5 sums file.
      -o, --output-dir OUTDIR   Output directory for dump files.
      -v, --verbose             Generate verbose output.
      -h, --help                Show this help message and exits.
      --version                 Print version and copyright information.
----
download.sh is part of wikidump.
download.sh needs docopts for CLI argument parsing.
EOF
)"

# CLI arguments
DATE="$date"
if [ -z "$date" ]; then
    DATE='last'
fi

OUTDIR="$output_dir/$PROJECT/$DATE"
if [ -z "$output_dir" ]; then
    OUTDIR="dumps/$PROJECT/$DATE"
fi

LIST="$list"
if [ -z "$list" ]; then
    LIST="$MD5FILE"
else
    md5_no_download=true
fi

FILTER="$filter"
if [ ! -z "$list" ]; then
    FILTER="history"
fi


if $verbose; then
    echo "--- Download info ---"
    echo "Project name: $PROJECT"
    echo "Dump date: $DATE"
    echo "Output directory: $OUTDIR"
    echo "List: $LIST"
    echo "Filter: $FILTER"
    echo "---"
fi

# global base URL
BASE_URL="http://dumps.wikimedia.org/$PROJECT/$DATE/"

# download the md5sum
# https://dumps.wikimedia.org/itwiki/20151002/itwiki-20151002-md5sums.txt
if $md5_no_download; then
    if $verbose; then
        echo ""
        echo "Skipping MD5 download"
        echo ""
    fi
else
    if $verbose; then
        echo ""
        echo "Dowloading MD5 sums file $BASE_URL/$MD5FILE ..."
        echo ""
    fi

    MD5FILE="$PROJECT-$DATE-md5sums.txt"
    aria2c "$BASE_URL/$MD5FILE"

    if [ ! -z "$md5_only" ]; then
        echo ""
        echo "---"
        echo "Dowloading MD5 sums done!"
        exit 0
    fi
fi

# create OUTDIR and all the necessary intermediate directories
mkdir -p "$OUTDIR"


cut -f 3 -d ' ' "$LIST" | grep "$FILTER" | \
  awk -v prefix=$BASE_URL '{print prefix $0}' | \
  xargs -n 1 aria2c -x 3 -s 3 -c --force-sequential --dir="$OUTDIR"
