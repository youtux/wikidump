'''wikidump
    ~~~~~~~~
    Extract features and stats from wikipedia XML dump files.

'''

from setuptools import setup, find_packages

setup(
    name='wikidump',
    version='0.0.1',
    author='Alessio Bogon',
    author_email='alessi' 'o.bogon' '<a' 't>' 'gm' 'ail' '<d' 'ot>co' 'm',
    license='GPL3',
    description='Extract features from wikipedia XML dumps.',
    long_description=__doc__,
    url='https://github.com/youtux/wikidump',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'wikidump=wikidump.__main__:main',
        ],
    },
    install_requires=[
        'Mako==1.0.2',
        'mediawiki-utilities==0.4.18',
        'mwcites==0.2.0',
        'mwcli==0.0.1',
        'mwtypes==0.2.0',
        'mwxml==0.2.0',
        'regex==2015.9.28',
        'more-itertools==2.2',
        'fuzzywuzzy==0.8.0',
        'python-Levenshtein==0.12.0',
    ],
)
