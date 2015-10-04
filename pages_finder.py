import sys
import subprocess
import os

import mwxml.element_iterator
import lxml.etree

def open_7z(filename):
    inside_filename, _ = os.path.splitext(
        os.path.basename(filename)
    )
    args = ['/usr/local/bin/7z', 'e', '-so', filename, inside_filename]
    proc = subprocess.Popen(args,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL,
                       )
    return proc.stdout


def trim_ns(tag):
    return tag[tag.find("}") + 1:]


def main():
    # pages_to_extract = sys.argv[1:]
    file_name = 'dumps/20150901/enwiki-20150901-pages-meta-history1.xml-p000000010p000002861.7z'
    f = open_7z(file_name)
    # root_element_handler(mwxml.element_iterator.ElementIterator.from_file(f))
    it = lxml.etree.iterparse(f, tag='{http://www.mediawiki.org/xml/export-0.10/}page')
    for event, elem in it:
        title = elem.find('{http://www.mediawiki.org/xml/export-0.10/}title').text
        if title != 'Autism':
            continue
        print("Start at line:", elem.sourceline)

        event, next_elem = next(it)
        print("finishes at line:", next_elem.sourceline)

        break



if __name__ == '__main__':
    main()
