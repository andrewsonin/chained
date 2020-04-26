from collections import abc
from typing import Iterable, Any, Callable, Union, Iterator, Generator

from lib.errors.functions import InfiniteSelfReferenceError
from lib.typing.typevar import T


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
        if isinstance(item, abc.Iterable) and not isinstance(item, (str, bytes)):
            yield from flat(item)
        else:
            yield item  # type: ignore


def has_inf_recursion(iterable: Iterable) -> bool:
    """
    Checks if an iterable has an infinite recursion to itself.

        >>> array = (3, 4, -1, [232, None, 'Jim', (3, [333, [333, 43]], b'Gregor')])
        >>> has_inf_recursion(array)
        False
        >>> array[-1].append(array)
        >>> array
        (3, 4, -1, [232, None, 'Jim', (3, [333, [333, 43]], b'Gregor'), (...)])
        >>> has_inf_recursion(array)
        True

    Args:
        iterable:  iterable of iterest
    Returns:
                   boolean indicating whether an iterable contains a reference to itself
    """

    def unravel(seq: Iterable) -> bool:
        for item in seq:
            if isinstance(item, abc.Iterable) and not isinstance(item, (str, bytes)):
                if item is iterable or unravel(item):
                    return True
        return False

    return unravel(iterable)


def flat_with_rec_check(iterable: Iterable[Union[T, Iterable]]) -> Generator[T, None, None]:
    """
    Flattens an iterable with any levels of nesting, yielding its values into a generator.
    Throws an exception if the iterable contains a reference to itself while reaching this reference.

        >>> array = (3, 4, -1, [232, None, 'Jim', (3, [333, [333, 43]], b'Gregor')])
        >>> tuple(flat(array))
        (3, 4, -1, 232, None, 'Jim', 3, 333, 333, 43, b'Gregor')

    Args:
        iterable:  iterable of iterest
    Throws:
        InfiniteSelfReferenceError(RecursionError)
                   in case of infinite recursion
    Returns:
                   resulting generator
    """

    def unravel(seq: Iterable) -> Iterator:
        for item in seq:
            if isinstance(item, abc.Iterable) and not isinstance(item, (str, bytes)):
                if item is iterable:
                    raise InfiniteSelfReferenceError('Iterable contains a reference to itself')
                yield from unravel(item)
            else:
                yield item

    yield from unravel(iterable)


def compose_map(predicates: Iterable[Callable[[Any], T]],
                iterable: Iterable) -> Generator[T, None, None]:
    """
    A composite analogue of the built-in function 'map' that allows the user to specify multiple mapping functions.
    They are executed sequentially from left to right.

        >>> tuple(
        >>>     compose_map(
        >>>         (lambda x: x ** 2, lambda x: x - 1, round),
        >>>         (1, 2, 3, 4, 8, 10)
        >>>     )
        >>> )
        (0, 3, 8, 15, 63, 99)

    Args:
        predicates:  functions to map
        iterable:    iterable to be transformed

    Returns:
                     resulting generator
    """
    if isinstance(predicates, abc.Iterator):
        predicates = tuple(predicates)
    for item in iterable:
        for pred in predicates:
            item = pred(item)
        yield item


def compose_multiarg_map(predicates: Iterable[Callable[..., T]],
                         iterable: Iterable) -> Generator[T, None, None]:
    """
    'compose_map' analogue that accepts multi-argument functions.

    These functions should return either a single value or a tuple of values.
    In the latter case, the returned tuple will be unpacked into the next function,
    but not passed as a single argument.

        >>> tuple(
        >>>     compose_multiarg_map(
        >>>         (
        >>>             lambda x, y:     (x * y, x - y, x + y),
        >>>             lambda x, y, z:   x + y + z,
        >>>             lambda x:        [x * x, x * 2],
        >>>             lambda array:     sum(array)
        >>>         ),
        >>>         (
        >>>             (1, 2),
        >>>             (3, 4),
        >>>             (5, 6)
        >>>         )
        >>>     )
        >>> )
        (24, 360, 1680)

    Args:
        predicates:  functions to map
        iterable:    iterable to be transformed

    Returns:
                     resulting generator
    """
    if isinstance(predicates, abc.Iterator):
        predicates = tuple(predicates)
    for item in iterable:
        for pred in predicates:
            if type(item) is tuple:
                item = pred(*item)
            else:
                item = pred(item)
        yield item


def compose_filter(predicates: Iterable[Callable[[Any], bool]],
                   iterable: Iterable[T]) -> Generator[T, None, None]:
    """
    A composite analogue of the built-in function 'filter' that allows the user to specify multiple filter functions.
    They are executed lazily and sequentially from left to right.

        >>> tuple(
        >>>     compose_filter(
        >>>         (lambda x: x > 2, lambda x: x < 10),
        >>>         (1, 2, 3, 4, 8, 10)
        >>>     )
        >>> )
        (3, 4, 8)

    Args:
        predicates:  filters to map
        iterable:    iterable to be filtered

    Returns:
                     resulting generator
    """
    if isinstance(predicates, abc.Iterator):
        predicates = tuple(predicates)
    for item in iterable:
        for pred in predicates:
            if not pred(item):
                break
        else:
            yield item


def compose_multiarg_filter(predicates: Iterable[Callable],
                            iterable: Iterable[T]) -> Generator[T, None, None]:
    """
    'compose_filter' analogue that accepts multi-argument functions.

    These functions should return either a single value or a tuple of values.
    In the latter case, the returned tuple won't be passed as a single argument to the next function,
    but will be unpacked into it.

    Passes only those values that are transformed to True (maybe implicitly)
    by the 'compose_multiarg_map' with the same arguments.

        >>> tuple(
        >>>     compose_multiarg_filter(
        >>>         (
        >>>             lambda x, y:     (x * y, x - y, x + y),
        >>>             lambda x, y, z:   x + y + z,
        >>>             lambda x:        [x * x, x * 2],
        >>>             lambda array:     sum(array)
        >>>         ),
        >>>         (
        >>>             ( 1, 2),  # 24    will be passed
        >>>             (-1, 0),  # 0     won't
        >>>             ( 3, 4),  # 360   will be passed
        >>>             ( 5, 6),  # 1680  will be passed
        >>>             ( 0, 0)   # 0     won't
        >>>         )
        >>>     )
        >>> )
        ((1, 2), (3, 4), (5, 6))  # Doesn't pass those values that are transformed to False by 'compose_multiarg_map'

    Args:
        predicates:  functions to map
        iterable:    iterable to be filtered

    Returns:
                     resulting generator
    """
    if isinstance(predicates, abc.Iterator):
        predicates = tuple(predicates)
    for item in iterable:
        transformed: Any = item
        for pred in predicates:
            if type(transformed) is tuple:
                transformed = pred(*transformed)
            else:
                transformed = pred(transformed)
        if transformed:
            yield item
