# wikidump

Extract some information from MediaWiki XML dumps.

## Installation
This project has been tested with Python 3.5.0, but should also work with Python 3.4.3.

You need to install dependencies first, as usual.
```sh
pip install -r requirements.txt
```

## Usage
You need to download Wikipiedia dumps first:
```sh
./download.sh
```

Then run the extractor:
```sh
python -m wikidump FILE [FILE ...] OUTPUT_DIR
```

It will take some time... RAM will not suffer, I promise.
