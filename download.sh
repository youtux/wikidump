#!/bin/sh

DATE='20150901'
LIST="enwiki-$DATE-md5sums.txt"
BASE_URL="http://dumps.wikimedia.org/enwiki/$DATE/"
OUT_DIR="dumps/$DATE"

mkdir -p "$OUT_DIR"

cut -f 3 -d ' ' "$LIST" | \
  awk -v prefix=$BASE_URL '{print prefix $0}' | \
  # wget -c "--directory-prefix=$OUT_DIR" -i -
  xargs -n 1 aria2c -x 3 -s 3 -c --force-sequential "--dir=$OUT_DIR"
