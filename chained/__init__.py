from collections import deque
from itertools import islice, chain, zip_longest, starmap, count
from types import GeneratorType, TracebackType, CodeType, FrameType
from typing import (

    # Type qualifiers
    Any,
    Final,
    Optional,
    Union,

    # Abstract base classes
    Type,
    Callable,
    Iterable,
    Iterator,
    Generator,
    Reversible,
    Sequence,

    # Abstract generic types
    Generic,

    # Concrete generic types
    Dict,
    Tuple,

    # Decorators and functions
    overload,

)

from chained.functions import flat, filter_map, compose_map, compose_filter, cleandoc_deco
from chained.type_utils import *
from chained.type_utils.meta import ChainedMeta
from chained.type_utils.protocol import varArgCallable
from chained.type_utils.typevar import *

__all__: Final = (
    # Classes
    'ChainIterable',
    'ChainIterator',
    'ChainGenerator',
    'ChainRange',
    'Range',

    # Functions and decorators
    'make_chain',
    'seq',
    'c'
)


def resolve_appropriate_container(cls):
    # TODO
    return ChainIterable


class ChainIterable(Generic[T_co], metaclass=ChainedMeta):
    """Wrapper object that provides convenient chain-like methods for any iterable."""

    # The order of the method definitions here
    # and in all descendants of the class must obey the following sequence.
    #
    # 1) __init__
    # 2) Other magic attributes
    # 3) Static methods
    # 4) Class methods
    # 5) Properties
    # 6) Ordinary methods
    #
    # Each group should be sorted lexicographically.

    __slots__ = ('_core',)

    @overload
    def __init__(self, iterable: Iterable[T_co], /) -> None:
        pass

    @overload
    def __init__(self, iterable: T_co, /, *iterables: T_co) -> None:
        pass

    def __init__(self, arg1: Union[Iterable[T_co], T_co], /, *args: T_co) -> None:
        """
        Wrapper object that provides convenient chain-like methods for any iterable.

        Possible __init__ signatures:

        (Iterable[T] | *T) -> None

        >>> ChainIterable(3, 4, 5)
        ChainIterable of (3, 4, 5)

        >>> ChainIterable((3, 4, 5))
        ChainIterable of (3, 4, 5)

        Args:
            arg1:   iterable if 'args' are not specified. Otherwise - the first value to iterate over
            *args:  any values to iterate over
        """
        if not args:
            if not hasattr(arg1, '__iter__'):
                raise TypeError(
                    'Cannot initialize an instance of `ChainIterable` '
                    f'from the instance of a non-iterable class {type(arg1)}'
                )
            self._core: Final[Iterable[T_co]] = arg1  # type: ignore
        else:
            self._core: Final[Tuple[T_co, ...]] = (arg1, *args)  # type: ignore

    @overload
    def __getitem__(self, item: int) -> Optional[int]:
        pass

    @overload
    def __getitem__(self, item: slice) -> 'ChainIterator[T_co]':
        pass

    def __getitem__(self, item: Union[int, slice]) -> Optional[Union[int, 'ChainIterator[T_co]']]:
        """
        Allows to access elements of 'self' by square brace indexing.
        Common use-case of throwing ``IndexError`` as a negative result of bound checking
        in case of single value selection is replaced by returning ``None``.

        >>> ChainIterable(range(0, 20, 2))[3:].collect(tuple)
        ChainIterable of (6, 8, 10, 12, 14, 16, 18)

        >>> ChainIterable(range(0, 20, 2))[3::2].collect(tuple)
        ChainIterable of (6, 10, 14, 18)

        Args:
            item:  `int` or `slice`
        Returns:
            if 'item' is `slice`, `ChainIterator` over the values selected. Otherwise, single value at the position
        """
        if isinstance(item, int):
            return next(islice(self._core, item, None), None)  # type: ignore
        return ChainIterator._make_with_no_checks(
            islice(self._core, item.start, item.stop, item.step)
        )

    def __iter__(self) -> Iterator[T_co]:
        """
        >>> type(ChainIterable(range(10)).__iter__())
        <class 'range_iterator'>

        Returns:
            Iterator of the wrapped iterable
        """
        return iter(self._core)

    def __repr__(self) -> str:
        """
        >>> ChainIterable((2, 4, 5)).__repr__()
        'ChainIterable of (2, 4, 5)'

        Returns:
            self-representation as string
        """
        return f'ChainIterable of {self._core}'

    @staticmethod
    def _make_with_no_checks(iterable: Iterable[T_co]) -> 'ChainIterable[T_co]':
        """
        Makes class instance with no safety checks.

        >>> ChainIterable._make_with_no_checks((2, 3, 11))
        ChainIterable of (2, 3, 11)

        >>> ChainIterable._make_with_no_checks(None)
        ChainIterable of None

        Args:
            iterable:  iterable to wrap around
        Returns:
            `ChainIterable` wrapper of the iterable
        """
        instance = ChainIterable.__new__(ChainIterable)
        instance._core = iterable  # type: ignore
        return instance

    @property
    def core(self) -> Iterable[T_co]:
        """
        Internal iterable access handler.

        >>> ChainIterable((1, 2, 3)).core
        (1, 2, 3)

        Returns:
            Raw iterable inside the 'self' instance
        """
        return self._core

    def all(self) -> bool:
        """
        Chained analogue of the built-in ``all`` function.

        >>> ChainIterable([True, True, False]).all()
        False

        >>> ChainIterable([1, 2, 3.4, 0, 1]).all()
        False

        >>> ChainIterable([1, 2, 3.4, 1]).all()
        True

        Returns:
            Whether all values of 'self' converts to True
        """
        return all(self._core)

    def any(self) -> bool:
        """
        Chained analogue of the built-in 'any' function.

        >>> ChainIterable([True, True, False]).any()
        True

        >>> ChainIterable([1, 2, 3.4, 0, 1]).any()
        True

        >>> ChainIterable([0, 0.0, False, ()]).any()
        False

        Returns:
            Whether at least one value of 'self' converts to True
        """
        return any(self._core)

    def chain(self: 'ChainIterable[M_co]', *iterables: Iterable[M_co]) -> 'ChainIterator[M_co]':
        """
        Takes an arbitrary number of 'iterables' and creates a new iterator over the 'self'
        and over each input iterable.

        >>> ChainIterable((3, 4, 5)).chain((6, 7, 8), [10, 13, 14]).collect(tuple)
        ChainIterable of (3, 4, 5, 6, 7, 8, 10, 13, 14)

        Args:
            *iterables:  iterables to "extend"
        Returns:
            A new iterator which will first iterate over the values from the 'self'
            and then over the values from the iterables
        """
        return ChainIterator._make_with_no_checks(
            chain(self._core, *iterables)
        )

    def chunks(self,
               chunk_size: int,
               collector: Callable[[Iterable[T_co]], Iterable[T_co]] = tuple) -> 'ChainIterator[Iterable[T_co]]':
        """
        Splits the 'self' into ``tuples`` of length `chunk_size`. Fills with 'pad_value' if necessary.

        >>> ChainIterable(range(10)).chunks(3).collect(tuple)
        ChainIterable of ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9,))

        >>> ChainIterable(range(10)).chunks(3, list).collect(tuple)
        ChainIterable of ([0, 1, 2], [3, 4, 5], [6, 7, 8], [9])

        Args:
            chunk_size:  size of eq_chunks
            collector:   chunk holder, can be any callable with signature (Iterable) -> Iterable
        Returns:
            zip iterator
        """

        def chunk_generator():
            iterator = iter(self._core)
            while chunk := collector(islice(iterator, chunk_size)):
                yield chunk

        return ChainIterator._make_with_no_checks(chunk_generator())

    def collect(self, collector: Callable[[Iterable[T_co]], Iterable[M]]) -> 'ChainIterable[M]':
        """
        Passes 'self' to 'collector'.

        >>> ChainIterable(range(5)).collect(list)
        ChainIterable of [0, 1, 2, 3, 4]

        >>> ChainIterable(range(0, 10, 2)).collect(tuple)
        ChainIterable of (0, 2, 4, 6, 8)

        Args:
            collector:  any callable with signature (Iterable) -> Iterable
        Returns:
            Result of this consumption wrapped in the instance of 'ChainIterable'
        """

        wrapper = resolve_appropriate_container(collector) if isinstance(collector, type) else ChainIterable  # TODO
        return wrapper(collector(self._core))

    def enumerate(self,
                  init_value: int = 0) -> 'ChainIterator[Tuple[int, T_co]]':
        """
        Creates an iterator which gives the current iteration count as well as the next value.

        >>> ChainIterable(range(3, 6)).enumerate(1).collect(tuple)
        ChainIterable of ((1, 3), (2, 4), (3, 5))

        Args:
            init_value:  initial value to count from
        Returns:
            resulting iterator
        """
        return ChainIterator._make_with_no_checks(enumerate(self._core, init_value))

    def eq_chunks(self, chunk_size: int) -> 'ChainIterator[Tuple[T_co, ...]]':
        """
        Splits the 'self' into tuples of length `chunk_size`.

        >>> ChainIterable(range(10)).eq_chunks(3).collect(tuple)
        ChainIterable of ((0, 1, 2), (3, 4, 5), (6, 7, 8))

        Args:
            chunk_size:  size of chunk
        Returns:
            zip iterator
        """
        return ChainIterator._make_with_no_checks(
            zip(*((iter(self._core),) * chunk_size))
        )

    def eq_chunks_with_pad(self, chunk_size: int, pad_value: Any = None) -> 'ChainIterator[Tuple[T_co, ...]]':
        """
        Splits the 'self' into ``tuples`` of length `chunk_size`. Fills with 'pad_value' if necessary.

        >>> ChainIterable(range(10)).eq_chunks_with_pad(3, 'pad').collect(tuple)
        ChainIterable of ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 'pad', 'pad'))

        Args:
            chunk_size:  size of eq_chunks
            pad_value:   padding value
        Returns:
            zip iterator
        """
        return ChainIterator._make_with_no_checks(
            zip_longest(
                *((iter(self._core),) * chunk_size),
                fillvalue=pad_value
            )
        )

    def filter(self, *predicates: Callable[[T_co], bool]) -> 'ChainIterator[T_co]':
        """
        Filters values of 'self', applying 'predicates' from left to right in a lazy manner.

        >>> ChainIterable(range(10)).filter(lambda x: x > 3, lambda x: x < 8).collect(tuple)
        ChainIterable of (4, 5, 6, 7)

        Args:
            *predicates:  predicates to apply
        Returns:
             resulting iterator
        """
        iterator = iter(self._core)
        for pred in predicates:
            iterator = filter(pred, iterator)
        return ChainIterator._make_with_no_checks(iterator)

    def filter_map(self,
                   function: Callable[[T_co], M_co],
                   exceptions: Union[Type[BaseException], Tuple[Type[BaseException], ...]]) -> 'ChainIterator[M_co]':
        """
        Creates an iterator that both filters and maps.
        The 'function' will be called to each value of 'self' and, if the 'exception' is not raised,
        the iterator will yield the result.

        >>> ChainIterable((1, 3, 4, 0, 0, 2)).filter_map(lambda x: round(1 / x, 3), ZeroDivisionError).collect(tuple)
        ChainIterable of (1.0, 0.333, 0.25, 0.5)

        >>> ChainIterable(('1', '0', '0', '2', 'ef'))                                         \
                .filter_map(lambda x: round(1 / int(x), 3), (ValueError, ZeroDivisionError))  \
                .collect(tuple)
        ChainIterable of (1.0, 0.5)

        Args:
            function:     function to map
            *exceptions:  exception to catch
        Returns:
            resulting iterator
        """
        return ChainIterator._make_with_no_checks(filter_map(function, self._core, exceptions))

    def first(self, default: Any = None) -> Optional[T_co]:
        """
        >>> ChainIterable(3, 4, 5).first()
        3

        >>> ChainIterable(()).first('default')
        'default'

        Args:
            default:  return value in case of 'self' is empty
        Returns:
            first value of 'self'
        """
        return next(iter(self._core), default)

    def flat(self) -> 'ChainIterator[T_co]':
        """
        Creates an iterator that flattens a nested structure. Removes all levels of indirection.
        Does not flatten ``str``, ``bytes`` and ``bytearray``.

        >>> ChainIterable([3, 4, 5, (6, 7, 8, [9, 10, [11], 12], 13)]).flat().collect(tuple)
        ChainIterable of (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)

        >>> ChainIterable([3, 4, 5, (6, 7, 8, [9, '10', [11], '12'], 13)]).flat().collect(tuple)
        ChainIterable of (3, 4, 5, 6, 7, 8, 9, '10', 11, '12', 13)

        Returns:
            resulting iterator
        """
        return ChainIterator._make_with_no_checks(flat(self._core))

    def foreach(self, function: Callable[[T_co], Any]) -> None:
        """
        Calls a 'function' for each argument, evaluating the 'self'.

        >>> ChainIterable((1, 2, 3)).foreach(lambda x: print(x - 1))
        0
        1
        2

        Args:
            function:  function to call
        Returns:
            None
        """
        deque(map(function, self._core), 0)

    def inspect(self, callback: Callable[[T_co], Any]) -> 'ChainIterator[T_co]':
        """
        Does something with each element of the 'self', passing the values on.

        >>> ChainIterable((1, 2, 3)).inspect(lambda x: print(x - 1)).collect(tuple)
        0
        1
        2
        ChainIterable of (1, 2, 3)

        Args:
            callback:  function to call
        Returns:
            resulting iterator
        """

        def inspector(x):
            callback(x)
            return x

        return ChainIterator._make_with_no_checks(map(inspector, self._core))

    def iter(self) -> 'ChainIterator[T_co]':
        """
        Converts 'self' to the instance of ``ChainIterator``.

        >>> str(ChainIterable(range(100)).iter())[:51]
        'ChainIterator wrapper of <range_iterator object at '

        Returns:
            Corresponding `ChainIterator`
        """
        return ChainIterator._make_with_no_checks(iter(self._core))

    def last(self, *, default: Any = None) -> Optional[T_co]:
        """
        Evaluates the 'self', returning the last element.

        >>> ChainIterable(range(10_000)).last()
        9999

        Args:
            default:  default value to return
        Returns:
            The last element if 'self' contains anything. 'default' - otherwise
        """
        last_elem = deque(self._core, 1)
        if last_elem:
            return last_elem[0]
        return default

    def last_n(self, n: int) -> 'ChainIterable[T_co]':
        """
        Evaluates the 'self', returns last `n` elements. Stores them into ``deque``.

        >>> ChainIterable(range(10_000)).last_n(5)
        ChainIterable of deque([9995, 9996, 9997, 9998, 9999], maxlen=5)

        Args:
            n:    number of last elements
        Returns:
            Last n elements container
        """
        return ChainIterable._make_with_no_checks(deque(self._core, n))

    def len_eval(self) -> int:
        """
        Evaluates the 'self', counting the number of iterations.

        >>> ChainIterable(i for i in range(1_000) if i % 2).len_eval()
        500

        Returns:
            The number of iterations
        """
        last_elem = deque(enumerate(self, 1), 1)
        if last_elem:
            return last_elem[0][0]
        return 0

    @overload
    def map(self, func: Callable[[T_co], T], /) -> 'ChainIterator[T]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            /) -> 'ChainIterator[T1]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            /) -> 'ChainIterator[T2]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            /) -> 'ChainIterator[T3]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            /) -> 'ChainIterator[T4]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            f4: Callable[[T4], T5],
            /) -> 'ChainIterator[T5]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            f4: Callable[[T4], T5],
            f5: Callable[[T5], T6],
            /) -> 'ChainIterator[T6]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            f4: Callable[[T4], T5],
            f5: Callable[[T5], T6],
            f6: Callable[[T6], T7],
            /) -> 'ChainIterator[T7]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            f4: Callable[[T4], T5],
            f5: Callable[[T5], T6],
            f6: Callable[[T6], T7],
            f7: Callable[[T7], T8],
            /) -> 'ChainIterator[T8]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            f4: Callable[[T4], T5],
            f5: Callable[[T5], T6],
            f6: Callable[[T6], T7],
            f7: Callable[[T7], T8],
            f8: Callable[[T8], T9],
            /) -> 'ChainIterator[T9]':
        pass

    @overload
    def map(self,
            func: Callable[[T_co], T],
            f0: Callable[[T], T1],
            f1: Callable[[T1], T2],
            f2: Callable[[T2], T3],
            f3: Callable[[T3], T4],
            f4: Callable[[T4], T5],
            f5: Callable[[T5], T6],
            f6: Callable[[T6], T7],
            f7: Callable[[T7], T8],
            f8: Callable[[T8], T9],
            f9: Callable[[T9], Any],
            /,
            *f: Callable[[Any], Any]) -> 'ChainIterator':
        pass

    def map(self,
            func: Callable[[T_co], T],
            /,
            *funcs: Callable[[Any], Any]) -> 'ChainIterator':
        """
        Maps functions to the values of the iterable.
        Functions are called sequentially in the the same order as they passed to the arguments.

        >>> ChainIterable(range(10)).map(lambda x: x - 1, str).collect(tuple)
        ChainIterable of ('-1', '0', '1', '2', '3', '4', '5', '6', '7', '8')

        Args:
            func:    first function to map
            *funcs:  remaining functions to map
        Returns:
            resulting iterator
        """
        iterator = map(func, self._core)
        for func in funcs:
            iterator = map(func, iterator)
        return ChainIterator._make_with_no_checks(iterator)

    def nth(self: 'ChainIterable[M_co]', n: int, default: Optional[M_co] = None) -> Optional[M_co]:
        """
        Evaluates the 'self' until the `n`-th element and then returns it.

        >>> ChainIterable(range(2, 12)).nth(5)
        7

        >>> ChainIterable(range(2, 12)).nth(500, 'Default')
        'Default'

        Args:
            n:        order number
            default:  default value to return

        Returns:
            The n-th element if the iterable contains it. 'default' - otherwise
        """
        return next(islice(self._core, n, None), default)

    def run(self) -> None:
        """
        Evaluates the entire 'self' and forgets about it.

        >>> ChainIterable(range(3)).map(print).run()
        0
        1
        2

        Returns:
            None
        """
        # Feeds the entire iterator of the corresponding iterable into a zero-length deque
        # https://docs.python.org/3/library/itertools.html#itertools-recipes
        deque(self._core, 0)

    def skip(self, n: int) -> 'ChainIterator[T_co]':
        """
        Creates an iterator that skips the first `n` elements of the 'self'.

        >>> ChainIterable(range(10)).skip(5).collect(tuple)
        ChainIterable of (5, 6, 7, 8, 9)

        >>> ChainIterable(range(10)).skip(50).collect(tuple)
        ChainIterable of ()

        Args:
            n:    number of items to skip
        Returns:
            slice iterator
        """
        iterator = iter(self._core)
        next(islice(iterator, n, n), None)
        return ChainIterator._make_with_no_checks(iterator)

    @overload
    def slice(self,
              stop: Optional[int],
              /) -> 'ChainIterator[T_co]':
        pass

    @overload
    def slice(self,
              start: Optional[int],
              stop: Optional[int],
              /) -> 'ChainIterator[T_co]':
        pass

    @overload
    def slice(self,
              start: Optional[int],
              stop: Optional[int],
              step: Optional[int],
              /) -> 'ChainIterator[T_co]':
        pass

    def slice(self,
              *args: Optional[int]) -> 'ChainIterator[T_co]':
        """
        Makes slice iterator over the 'self'.

        >>> ChainIterable(range(1_000))[100:200:20].collect(tuple)
        ChainIterable of (100, 120, 140, 160, 180)

        Args:
            *args:  slicing parameters: ([start,] stop[, step])
        Returns:
            slice iterator
        """
        return ChainIterator._make_with_no_checks(
            islice(self._core, *args)
        )

    def starmap(self: 'ChainIterable[Iterable[M_co]]',
                func: Callable,
                /,
                *funcs: Callable) -> 'ChainIterator':
        """
        Make an iterator that computes the function using arguments obtained from the iterable.
        Used instead of ``map`` when argument parameters are already grouped in tuples from a single iterable
        (the data has been “pre-zipped”).

        The difference between ``map`` and ``starmap`` parallels the distinction between function(a,b) and function(*c).
        Arguments (functions) of ``starmap`` are called sequentially in the the same order as they passed.

        >>> seq(1, ..., 10).chunks(3).starmap(lambda x, y, z: x * (y - z)).collect(tuple)
        ChainIterable of (-1, -4, -7)

        Args:
            func:    first function to map
            *funcs:  remaining functions to map
        Returns:
            resulting iterator
        """
        iterator = starmap(func, self._core)
        for func in funcs:
            iterator = starmap(func, iterator)
        return ChainIterator._make_with_no_checks(iterator)

    def split(self,
              n: int,
              collector: Callable[[Iterable[T_co]], Sequence[T_co]] = tuple) -> 'ChainIterator[Sequence[T_co]]':
        """
        Splits the 'self' into 'n' equal pieces, if possible.
        If not, the first few pieces will be 1 longer than the last few.

        >>> seq(1, ..., 12).split(5).collect(tuple)
        ChainIterable of ((1, 2, 3), (4, 5), (6, 7), (8, 9), (10, 11))

        >>> seq(1, ..., 10).split(3).collect(tuple)
        ChainIterable of ((1, 2, 3), (4, 5, 6), (7, 8, 9))

        >>> split_1, split_2, split_3 = seq(1, ..., 12).split(3)

        Args:
            n:          number of pieces
            collector:  split holder
        Returns:
            split iterator
        """

        core = collector(self._core)
        split_size, remainder = divmod(len(core), n)
        n_elements = [split_size] * n
        for i in range(min(n, remainder)):
            n_elements[i] += 1

        def split_generator() -> Generator[Sequence[T_co], None, None]:
            container = core
            first = last = 0
            for n in n_elements:
                last += n
                yield container[first:last]
                first = last

        return ChainIterator._make_with_no_checks(split_generator())

    def step_by(self, step: int) -> 'ChainIterator[T_co]':
        """
        Returns every `step`-th item of the 'self' as an iterator.

        >>> ChainIterable(range(10_000)).step_by(2343).collect(tuple)
        ChainIterable of (0, 2343, 4686, 7029, 9372)

        Args:
            step:  number of iterations to skip
        Returns:
            islice iterator
        """
        return ChainIterator._make_with_no_checks(
            islice(self._core, None, None, step)
        )

    def take(self, n: int) -> 'ChainIterator[T_co]':
        """
        Returns an iterator over the first `n` items of the 'self'.

        >>> ChainIterable(range(1_000)).take(5).collect(tuple)
        ChainIterable of (0, 1, 2, 3, 4)

        Args:
            n:    number of items
        Returns:
            slice iterator
        """
        return ChainIterator._make_with_no_checks(
            islice(self._core, n)
        )

    def transpose(self: 'ChainIterable[Iterable[M_co]]') -> 'ChainIterator[Tuple[M_co, ...]]':
        """
        Transposes the 'self' if it iterates over other iterables.
        Be careful: The first-order iterable will be evaluated.

        >>> ChainIterable([(1, 2), (3, 4), (5, 6)]).transpose().collect(tuple)
        ChainIterable of ((1, 3, 5), (2, 4, 6))

        Returns:
            zip iterator
        """
        return ChainIterator._make_with_no_checks(zip(*self._core))

    def unpack(self, receiver: varArgCallable[T_co, T]) -> T:
        """
        Unpacks the 'self' into the 'receiver'.

        >>> ChainIterable([(3, 4, 5), (6, 7, 8), (9, 10)]).unpack(lambda *args: '__'.join(map(str, args)))
        '(3, 4, 5)__(6, 7, 8)__(9, 10)'

        Args:
            receiver:  receiver to unpack into. It can be callable or `type` object
        Returns:
            Result of receiver.__call__(*self)
        """
        return receiver(*self._core)

    def zip(self: 'ChainIterable[M_co]',
            *iterables: Iterable[M_co]) -> 'ChainIterator[Tuple[M_co, ...]]':
        """
        Takes an arbitrary number of iterables and "zips up" the 'self' with them into a single iterator of tuples.

        >>> ChainIterable(1, 2, 3).zip((4, 5, 6), (7, 8)).collect(tuple)
        ChainIterable of ((1, 4, 7), (2, 5, 8))

        Args:
            *iterables:  iterables to "zip up"
        Returns:
            A new iterator that will iterate over other iterables,
            returning `tuples` where the first element comes from the 'self',
            and the n-th element comes from the (n-1)-th iterable from the 'iterables'.
        """
        return ChainIterator._make_with_no_checks(
            zip(self._core, *iterables)
        )


class ChainIterator(ChainIterable[T_co]):
    """``ChainIterable`` iterator"""

    __slots__ = ()

    def __init__(self, iterable: Iterable[T_co]) -> None:
        """
        ``ChainIterable`` iterator.

        Args:
            iterable:  iterable object to wrap in
        """
        self._core: Final = iter(iterable)  # type: ignore

    def __iter__(self) -> Iterator[T_co]:
        return self._core

    def __next__(self) -> T_co:
        return next(self._core)

    def __repr__(self) -> str:
        return f'ChainIterator wrapper of {self._core}'

    @staticmethod
    def _make_with_no_checks(iterator: Iterator[T_co]) -> 'ChainIterator[T_co]':  # type: ignore
        """
        Makes class instance with no safety checks.

        Args:
            iterator:  iterator to wrap around

        Returns:
            `ChainIterator` wrapper of the iterator
        """
        instance = ChainIterator.__new__(ChainIterator)
        instance._core = iterator  # type: ignore
        return instance

    @property
    def core(self) -> Iterator[T_co]:
        """
        Internal iterator access handler.

        Returns:
            Raw iterator inside the 'self' instance
        """
        return self._core

    def iter(self) -> 'ChainIterator[T_co]':
        return self

    def skip(self, n: int) -> 'ChainIterator[T_co]':
        next(islice(self._core, n, n), None)
        return self


class ChainReversible(ChainIterable[T_co]):
    __slots__ = ()

    @overload
    def __init__(self, iterable: Reversible[T_co], /) -> None:
        pass

    @overload
    def __init__(self, iterable: T_co, /, *iterables: T_co) -> None:
        pass

    def __init__(self, arg1: Union[Reversible[T_co], T_co], /, *args: T_co) -> None:
        """
        Wrapper object that provides convenient chain-like methods for any reversible.

        Possible __init__ signatures:

        (Reversible[T] | *T) -> None

        >>> ChainReversible(3, 4, 5)    # OK
        ChainReversible of (3, 4, 5)

        >>> ChainReversible((3, 4, 5))  # OK
        ChainReversible of (3, 4, 5)

        Args:
            arg1:   reversible if 'args' are not specified. Otherwise - the first value to iterate over
            *args:  any values to iterate over
        """
        if not args:
            if not hasattr(arg1, '__iter__') and not hasattr(arg1, '__reversed__'):
                raise TypeError(
                    'Cannot initialize an instance of `ChainReversible` '
                    f'from the instance of a non-reversible class {type(arg1)}'
                )
            self._core: Final[Reversible[T_co]] = arg1  # type: ignore
        else:
            self._core: Final[Tuple[T_co, ...]] = (arg1, *args)  # type: ignore

    def __repr__(self) -> str:
        return f'ChainReversible of {self._core}'

    def __reversed__(self) -> Iterator[T_co]:
        return reversed(self._core)

    @staticmethod
    def _make_with_no_checks(reversible: Reversible[T_co]) -> 'ChainReversible[T_co]':  # type: ignore
        """
        Makes class instance with no safety checks.

        >>> ChainReversible._make_with_no_checks((2, 3, 11))
        ChainReversible of (2, 3, 11)

        >>> ChainReversible._make_with_no_checks(None)
        ChainReversible of None

        Args:
            reversible:  iterable to wrap around
        Returns:
            `ChainIterable` wrapper of the iterable
        """
        instance = ChainReversible.__new__(ChainReversible)
        instance._core = reversible  # type: ignore
        return instance

    def reverse(self) -> ChainIterator[T_co]:
        """
        >>> ChainReversible(2, 3, 4).reverse().collect(tuple)
        ChainIterable of (4, 3, 2)

        Returns:
            reversed iterator
        """
        return ChainIterator._make_with_no_checks(reversed(self._core))


class ChainGenerator(ChainIterator[T_co], Generic[T_co, T_contra, M_co]):
    """Wrapper object that provides convenient chain-like methods for any ``generator``."""
    __slots__ = ()

    def __init__(self, generator: Generator[T_co, T_contra, M_co]) -> None:
        """
        ``ChainGenerator`` is a chained analogue of the built-in ``generator`` object.

        Args:
            generator:  stack frame to store
        """

        if not isinstance(generator, GeneratorType):
            if isinstance(generator, ChainGenerator):
                generator = generator._core
            else:
                raise TypeError(
                    f'{self.__class__.__name__} does not accept non-generator instances of {type(generator)}'
                )

        self._core: Final[Generator[T_co, T_contra, M_co]] = generator  # type: ignore

    def __iter__(self) -> Iterator[T_co]:
        return iter(self._core)

    def __next__(self) -> T_co:
        return next(self._core)

    def __repr__(self) -> str:
        return f'<ChainGenerator at {hex(id(self))}>'

    @staticmethod
    def _make_with_no_checks(  # type: ignore
            generator: Generator[T_co, T_contra, M_co]) -> 'ChainGenerator[T_co, T_contra, M_co]':
        """
        Makes class instance with no safety checks.

        Args:
            generator:  generator to wrap around
        Returns:
            `ChainGenerator` wrapper of the generator
        """
        instance = ChainGenerator.__new__(ChainGenerator)
        instance._core = generator  # type: ignore
        return instance

    @property
    def core(self) -> Generator[T_co, T_contra, M_co]:
        """
        Internal generator access handler.

        Returns:
            Raw generator inside the 'self' instance
        """
        return self._core

    @property
    def gi_code(self) -> CodeType:
        return self._core.gi_code

    @property
    def gi_frame(self) -> FrameType:
        return self._core.gi_frame

    @property
    def gi_running(self) -> bool:
        return self._core.gi_running

    @property
    def gi_yieldfrom(self) -> Optional[Generator]:
        return self._core.gi_yieldfrom

    def close(self) -> None:
        self._core.close()

    def send(self, value: T_contra) -> T_co:
        return self._core.send(value)

    def throw(self,
              exception: Type[BaseException],
              value: Any = None,
              traceback: Optional[TracebackType] = None) -> Any:
        return self._core.throw(exception, value, traceback)


class ChainRange(ChainIterable[int]):
    """Chained analogue of the built-in ``range`` object."""

    __slots__ = ()

    @overload
    def __init__(self, rng: range, /) -> None:
        pass

    @overload
    def __init__(self, stop: int, /) -> None:
        pass

    @overload
    def __init__(self, start: int, stop: int, /) -> None:
        pass

    @overload
    def __init__(self, start: int, stop: int, step: int, /) -> None:
        pass

    def __init__(self, *args) -> None:
        """
        ``ChainRange`` is a chained analogue of the built-in ``range`` object.

        Args:
            *args:  single `range` or `range` init parameters: [start,] stop[, step]
        """
        try:
            self._core: Final[range] = range(*args)  # type: ignore
        except TypeError:
            if len(args) == 1 and isinstance(range_candidate := args[0], range):
                self._core: Final[range] = range_candidate  # type: ignore
            else:
                raise

    def __contains__(self, item: int) -> bool:
        return item in self._core

    @overload  # type: ignore
    def __getitem__(self, key: int) -> int:
        pass

    @overload
    def __getitem__(self, key: slice) -> 'ChainRange':
        pass

    def __getitem__(self, key: Union[int, slice]) -> Union[int, 'ChainRange']:
        """
        Allows to access elements of 'self' by square brace indexing.
        Common use-case of throwing ``IndexError`` as a negative result of bound checking
        in case of single value selection is replaced by returning ``None``.

        >>> ChainRange(0, 20, 2)[3:].collect(tuple)
        ChainIterable of (6, 8, 10, 12, 14, 16, 18)

        >>> ChainRange(0, 20, 2)[3::2].collect(tuple)
        ChainIterable of (6, 10, 14, 18)

        Args:
            key:  `int` or `slice`
        Returns:
            if 'item' is `slice`, `ChainRange` over the values selected. Otherwise, single value at the position
        """
        if isinstance(key, slice):
            return ChainRange._make_with_no_checks(self._core[key])
        return self._core[key]

    def __iter__(self) -> Iterator[int]:
        return iter(self._core)

    def __len__(self) -> int:
        return len(self._core)

    def __repr__(self) -> str:
        return f'ChainRange({self._core.__repr__()[6:-1]})'

    def __reversed__(self) -> Iterator[int]:
        return reversed(self._core)

    @staticmethod
    def _make_with_no_checks(rng: range) -> 'ChainRange':  # type: ignore
        """
        Makes class instance with no safety checks.

        Args:
            rng:  `range` object to wrap around
        Returns:
            `ChainRange` wrapper of the range
        """
        instance = ChainRange.__new__(ChainRange)
        instance._core = rng  # type: ignore
        return instance

    @property
    def core(self) -> range:
        """
        Internal iterable access handler.

        >>> ChainRange(1, 232, 3).core
        range(1, 232, 3)

        Returns:
            Raw `range` object inside the 'self' instance
        """
        return self._core

    def count(self, value: int) -> int:
        return self._core.count(value)

    def index(self, value: int) -> int:
        return self._core.index(value)

    def len(self) -> int:
        """
        Returns the length of the range. Does not iterate anything.

        >>> ChainRange(1, 232, 3).len()
        77

        Returns:
            range length
        """
        return len(self._core)


# Cache dict for storing already created class - to - chain-class associations
_registered_chain_classes: Final[Dict] = {
    GeneratorType: ChainGenerator,
    range: ChainRange
}


@overload
def seq(start: int, ell: 'ellipsis', /) -> ChainIterator[int]:
    pass


@overload
def seq(start: int, ell: 'ellipsis', end: int, /) -> ChainRange:
    pass


@overload
def seq(start: int, second: int, ell: 'ellipsis', /) -> ChainIterator[int]:
    pass


@overload
def seq(start: int, second: int, ell: 'ellipsis', end: int, /) -> ChainRange:
    pass


@overload
def seq(start: int, ell: 'ellipsis', /, *, last: int) -> ChainRange:
    pass


@overload
def seq(start: int, second: int, ell: 'ellipsis', /, *, last: int) -> ChainRange:
    pass


@overload
def seq(*args: int) -> ChainIterable[int]:
    pass


@cleandoc_deco
def seq(*args: Union[int, 'ellipsis'], last: Optional[int] = None) -> ChainIterable[int]:
    """
    Creates a sequence that can be one of the following seven types.

    >>> seq(3, ...)              # [3, +∞)                 # step = 1
    ChainIterator wrapper of count(3)

    >>> seq(3, ..., 10)          # [3, 10)                 # step = 1
    ChainRange(3, 10)

    >>> seq(2, 5, ...)           # [2, 5, 8, 11, ..., +∞)  # step = 3
    ChainIterator wrapper of count(2, 3)

    >>> seq(2, 5, ..., 10)       # [2, 5, 8]               # step = 3
    ChainRange(2, 10, 3)

    >>> seq(2, ..., last=5)      # [2, 5]                  # step = 1
    ChainRange(2, 6)

    >>> seq(2, 4, ..., last=10)  # [2, 4, 6, 8, 10]        # step = 2
    ChainRange(2, 11, 2)

    >>> seq(1, 3, -1, -22, 1)    # [1, 3, -1, -22, 1]      # arbitrary sequence
    ChainIterable of (1, 3, -1, -22, 1)

    Args:
        *args:  positional arguments as in the examples
        last:   optional last element of the sequence
    Returns:
        resulting sequence
    """
    for i, elem in enumerate(args):
        if elem is Ellipsis:
            break
    else:
        return ChainIterable._make_with_no_checks(args)  # type: ignore

    arg_length = len(args)
    left_bound = args[0]

    if i == 1:

        if arg_length == 2:
            if last is None:
                return ChainIterator._make_with_no_checks(count(left_bound))  # type: ignore
            return ChainRange(left_bound, last + 1)  # type: ignore

        if arg_length == 3:
            if last is not None:
                raise ValueError(
                    "Parameter 'last' should not be defined "
                    'if positional arguments obey the following pattern: (start, ..., stop)'
                )
            return ChainRange(left_bound, args[-1])  # type: ignore

        raise IndexError(
            'The number of positional arguments should not exceed 3 '
            'in the case when the Ellipsis is in the 1st index position. '
            '(start, ...), (start, ..., stop), (arg1, ..., last=last) signatures are only allowed'
        )

    if i == 2:

        step = args[1] - left_bound  # type: ignore
        if arg_length == 3:
            if last is None:
                return ChainIterator._make_with_no_checks(count(left_bound, step))  # type: ignore
            return ChainRange(left_bound, last + 1, step)  # type: ignore

        if arg_length == 4:
            if last is not None:
                raise ValueError(
                    "Parameter 'last' should not be defined "
                    'if positional arguments obey the following pattern: (start, second, ..., stop)'
                )
            return ChainRange(left_bound, args[-1], step)  # type: ignore

        raise IndexError(
            'The number of positional arguments should not exceed 4 '
            'in the case when the Ellipsis is in the 2st index position. (start, second, ...), '
            '(start, second, ..., stop), (arg1, second, ..., last=last) signatures are only allowed'
        )

    raise IndexError(
        'Ellipsis can be a placeholder only at the 1st or the 2nd index positions'
    )


@overload
def make_chain(iterable: Iterator[T]) -> ChainIterator[T]:
    pass


@overload
def make_chain(iterable: Iterable[T]) -> ChainIterable[T]:
    pass


def make_chain(iterable: Iterable[T]) -> ChainIterable[T]:
    # TODO
    if hasattr(iterable, '__iter__'):
        if hasattr(iterable, '__next__'):
            return ChainIterator._make_with_no_checks(iterable)  # type: ignore
        return ChainIterable._make_with_no_checks(iterable)
    raise TypeError('')


c = seq
Range = ChainRange
