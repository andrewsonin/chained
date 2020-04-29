from typing import Iterable, Any, Callable, Generator

from chained.typing.typevar import T


def compose_map(iterable: Iterable, *predicates: Callable[[Any], T]) -> Generator[T, None, None]:
    """
    A composite analogue of the built-in function 'map' that allows the user to specify multiple mapping functions.
    They are executed sequentially from left to right.

        >>> tuple(
        >>>     compose_map(
        >>>         (1, 2, 3, 4, 8, 10),
        >>>
        >>>         lambda x: x ** 2,
        >>>         lambda x: x - 1,
        >>>         round
        >>>     )
        >>> )
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


def compose_multiarg_map(iterable: Iterable, *predicates: Callable[..., T]) -> Generator[T, None, None]:
    """
    'compose_map' analogue that accepts multi-argument functions.

    These functions should return either a single value or a tuple of values.
    In the latter case, the returned tuple will be unpacked into the next function,
    but not passed as a single argument.

        >>> tuple(
        >>>     compose_multiarg_map(
        >>>         (
        >>>             (1, 2),
        >>>             (3, 4),
        >>>             (5, 6)
        >>>         ),
        >>>
        >>>         lambda x, y:     (x * y, x - y, x + y),
        >>>         lambda x, y, z:   x + y + z,
        >>>         lambda x:        [x * x, x * 2],
        >>>         lambda array:     sum(array)
        >>>     )
        >>> )
        (24, 360, 1680)

    Args:
        predicates:  functions to map
        iterable:    iterable to be transformed

    Returns:
                     resulting generator
    """
    for item in iterable:
        for pred in predicates:
            if type(item) is tuple:
                item = pred(*item)
            else:
                item = pred(item)
        yield item


def compose_filter(iterable: Iterable[T], *predicates: Callable[[Any], bool]) -> Generator[T, None, None]:
    """
    A composite analogue of the built-in function 'filter' that allows the user to specify multiple filter functions.
    They are executed lazily and sequentially from left to right.

        >>> tuple(
        >>>     compose_filter(
        >>>         (1, 2, 3, 4, 8, 10),
        >>>
        >>>         lambda x: x > 2,
        >>>         lambda x: x < 10
        >>>     )
        >>> )
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


def compose_multiarg_filter(iterable: Iterable[T], *predicates: Callable) -> Generator[T, None, None]:
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
        >>>             ( 1, 2),  # 24    will be passed
        >>>             (-1, 0),  # 0     won't
        >>>             ( 3, 4),  # 360   will be passed
        >>>             ( 5, 6),  # 1680  will be passed
        >>>             ( 0, 0)   # 0     won't
        >>>         ),
        >>>
        >>>         lambda x, y:     (x * y, x - y, x + y),
        >>>         lambda x, y, z:   x + y + z,
        >>>         lambda x:        [x * x, x * 2],
        >>>         lambda array:     sum(array)
        >>>     )
        >>> )
        ((1, 2), (3, 4), (5, 6))  # Doesn't pass those values that are transformed to False by 'compose_multiarg_map'

    Args:
        predicates:  functions to map
        iterable:    iterable to be filtered

    Returns:
                     resulting generator
    """
    for item in iterable:
        transformed: Any = item
        for pred in predicates:
            if type(transformed) is tuple:
                transformed = pred(*transformed)
            else:
                transformed = pred(transformed)
        if transformed:
            yield item
