"""Various utilities."""

import functools
import regex as re
import sys
from typing import (NamedTuple, Generic, TypeVar, Iterable, List, Tuple,
                    Optional, T)

import more_itertools


class Diff(NamedTuple("Diff", [("action", str), ("data", T)]), Generic[T]):
    """Class representing diff between two iterables."""
    pass


T = TypeVar('T')
def diff(previous: Iterable[T], current: Iterable[T]) -> List[Diff[T]]:
    """Return a diff given the two iterables."""
    # previous = [ref.text for ref in previous]
    # current = [ref.text for ref in current]

    added = set(current) - set(previous)
    removed = set(previous) - set(current)

    diffs = (
        [Diff('added', el) for el in added]
        + [Diff('removed', el) for el in removed]
    )

    return diffs


# https://github.com/shazow/unstdlib.py/blob/master/unstdlib/standard/list_.py#L149
def listify(fn=None, wrapper=list):
    """
    A decorator which wraps a function's return value in ``list(...)``.

    Useful when an algorithm can be expressed more cleanly as a generator but
    the function should return an list.

    Example::

        >>> @listify
        ... def get_lengths(iterable):
        ...     for i in iterable:
        ...         yield len(i)
        >>> get_lengths(["spam", "eggs"])
        [4, 4]
        >>>
        >>> @listify(wrapper=tuple)
        ... def get_lengths_tuple(iterable):
        ...     for i in iterable:
        ...         yield len(i)
        >>> get_lengths_tuple(["foo", "bar"])
        (3, 3)
    """
    def listify_return(fn):
        @functools.wraps(fn)
        def listify_helper(*args, **kw):
            return wrapper(fn(*args, **kw))
        return listify_helper
    if fn is None:
        return listify_return
    return listify_return(fn)


T = TypeVar('T')
def iter_with_prev(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    """Iterate over an iterable, yielding the previous and the current element.
    """
    last = None
    for el in iterable:
        yield last, el
        last = el


def dot(num: Optional[int]=None) -> None:
    """Write a dot "." to the stderr stream."""
    if not num:
        what = '.'
    elif num < 10:
        what = str(num)
    else:
        what = '>'
    print(what, end='', file=sys.stderr, flush=True)


def log(*args):
    """Wrapper for "print" that writes on stderr, without newline."""
    first, *rest = args
    print('\n' + str(first), *rest, end='', file=sys.stderr, flush=True)


def remove_comments(source: str) -> str:
    """Remove all the html comments from a string."""
    pattern = re.compile(r'<!--(.*?)-->', re.MULTILINE | re.DOTALL)
    return pattern.sub('', source)


def has_next(peekable: more_itertools.peekable) -> bool:
    """Return True if the peekable has a next element."""
    try:
        peekable.peek()
        return True
    except StopIteration:
        return False
