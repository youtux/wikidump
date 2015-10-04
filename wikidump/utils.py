import functools
import os
import subprocess


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


def iter_with_prev(iterable):
    last = None
    for el in iterable:
        yield last, el
        last = el

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
