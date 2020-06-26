from collections import abc
from inspect import cleandoc
from types import FunctionType
from typing import Union, Type, Tuple, Iterable, Any, Callable, Generator

from chained.type_utils.typevar import T, M


def cleandoc_deco(func: T) -> T:
    """
    Cleans the function docstring.

    >>> def fun(x):        \
            '  DocString '
    >>> fun = cleandoc_deco(fun)
    >>> fun.__doc__
    'DocString '

    Args:
        func:  function whose documentation needs to be cleaned
    Returns:
        resulting function
    """
    if type(func) is FunctionType:
        doc_str = func.__doc__
        if doc_str is not None:
            func.__doc__ = cleandoc(doc_str)
    return func


@cleandoc_deco
def filter_map(function: Callable[[T], M],
               iterable: Iterable[T],
               exceptions: Union[Type[BaseException], Tuple[Type[BaseException], ...]]) -> Generator[M, None, None]:
    """
    Creates an iterator that both filters and maps.
    The 'function' will be called to each value and if the 'exception' is not raised the iterator yield the result.

    >>> tuple(                                  \
            filter_map(                         \
                lambda x: round(1 / int(x), 3), \
                ('1', '0', '0', '2', 'ef'),     \
                (ValueError, ZeroDivisionError) \
            )                                   \
        )
    (1.0, 0.5)

    Args:
        function:     function to map
        iterable:     iterable
        *exceptions:  exception to catch
    Returns:
        resulting iterator
    """
    for item in iterable:
        try:
            yield function(item)
        except exceptions:
            pass


@cleandoc_deco
def flat(iterable: Iterable[Union[T, Iterable]]) -> Generator[T, None, None]:
    """
    Flattens an iterable with any levels of nesting, yielding its values into a generator.

        >>> array = (3, 4, -1, [232, None, 'Jim', (3, [333, [333, 43]], b'Gregor')])
        >>> tuple(flat(array))
        (3, 4, -1, 232, None, 'Jim', 3, 333, 333, 43, b'Gregor')

    Args:
        iterable:  iterable of iterest
    Returns:
                   resulting generator
    """
    for item in iterable:
        if isinstance(item, abc.Iterable) and not isinstance(item, (str, bytes, bytearray)):
            yield from flat(item)
        else:
            yield item  # type: ignore


@cleandoc_deco
def compose_map(iterable: Iterable, *predicates: Callable[[Any], T]) -> Generator[T, None, None]:
    """
    A composite analogue of the built-in function 'map' that allows the user to specify multiple mapping functions.
    They are executed sequentially from left to right.

        >>> tuple(                       \
                compose_map(             \
                    (1, 2, 3, 4, 8, 10), \
                                         \
                    lambda x: x ** 2,    \
                    lambda x: x - 1,     \
                    round                \
                )                        \
            )
        (0, 3, 8, 15, 63, 99)

    Args:
        predicates:  functions to map
        iterable:    iterable to be transformed

    Returns:
                     resulting generator
    """
    for item in iterable:
        for pred in predicates:
            item = pred(item)
        yield item


@cleandoc_deco
def compose_filter(iterable: Iterable[T], *predicates: Callable[[Any], bool]) -> Generator[T, None, None]:
    """
    A composite analogue of the built-in function 'filter' that allows the user to specify multiple filter functions.
    They are executed lazily and sequentially from left to right.

        >>> tuple(                       \
                compose_filter(          \
                    (1, 2, 3, 4, 8, 10), \
                                         \
                    lambda x: x > 2,     \
                    lambda x: x < 10     \
                )                        \
            )
        (3, 4, 8)

    Args:
        predicates:  filters to map
        iterable:    iterable to be filtered

    Returns:
                     resulting generator
    """
    for item in iterable:
        for pred in predicates:
            if not pred(item):
                break
        else:
            yield item
