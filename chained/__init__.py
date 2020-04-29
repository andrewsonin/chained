from abc import abstractmethod
from collections import abc, deque
from itertools import islice, chain
from sys import getrefcount
from types import GeneratorType, TracebackType, CodeType, FrameType
from typing import (

    # Type qualifiers
    Any,
    Final,
    Literal,
    Optional,
    Union,

    # Abstract base classes
    Type,
    Callable,
    Iterable,
    Iterator,
    Generator,
    Sequence,

    # Generic types
    Dict,
    Tuple,
    Generic,

    # Decorators and functions
    overload

)

import chained.typing.protocol as protocol
from chained.functions import flat, filter_map
from chained.functions.optimized import (
    compose_map,
    compose_filter,
    compose_multiarg_map,
    compose_multiarg_filter
)
from chained.typing.typevar import T, T_co, M_co, T_contra

__all__: Final = (
    # Classes
    'ChainIterator',
    'ChainGenerator',
    'ChainRange',
    'ChainList',
    'ChainTuple',
    'ChainZip',
    'ChainFilter',
    'ChainMap',
    'ISlice',
    'Chain',
    # Functions and decorators
    'make_chain_class',
    'make_chain'
)


class AbstractChainIterable(protocol.singleArgInitializable[T_co], Generic[T_co]):
    @abstractmethod
    def __iter__(self) -> 'Iterator[T_co]':
        pass

    def iter(self) -> 'ChainIterator[T_co]':
        return ChainIterator(self.__iter__())

    @overload
    def map(self,
            predicate: Callable[[T_co], T],
            *,
            to_chain_class: Literal[True] = True) -> 'ChainMap[T_co, T]':
        pass

    @overload
    def map(self,
            predicate: Callable[[T_co], T],
            *,
            to_chain_class: Literal[False] = False) -> Iterator[T]:
        pass

    def map(self,
            predicate: Callable[[T_co], T],
            *,
            to_chain_class: bool = True) -> Union[Iterator[T], 'ChainMap[T_co, T]']:
        """
        Behaves similarly to the built-in function 'map'.

        Args:
            predicate:       function to map
            to_chain_class:  type of return value.
                            `Chained` map if True, built-in 'map' if False
        Returns:
            resulting iterator
        """
        if to_chain_class:
            return ChainMap(predicate, self)
        return map(predicate, self)

    @overload
    def filter(self,
               predicate: Callable[[T_co], bool],
               *,
               to_chain_class: Literal[True] = True) -> 'ChainFilter[T_co]':
        pass

    @overload
    def filter(self,
               predicate: Callable[[T_co], bool],
               *,
               to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def filter(self,
               predicate: Callable[[T_co], bool],
               *,
               to_chain_class: bool = True) -> Union[Iterator[T_co], 'ChainFilter[T_co]']:
        """
        Behaves similarly to the built-in function 'filter'.

        Args:
            predicate:       function to be filtered by
            to_chain_class:  type of return value.
                            `Chained` filter if True, built-in 'filter' if False
        Returns:
            resulting iterator
        """
        if to_chain_class:
            return ChainFilter(predicate, self)
        return filter(predicate, self)

    @overload
    def filter_map(self,
                   function: Callable[[T_co], M_co],
                   *exceptions: Type[BaseException],
                   to_chain_class: Literal[True] = True) -> 'ChainIterator[M_co]':
        pass

    @overload
    def filter_map(self,
                   function: Callable[[T_co], M_co],
                   *exceptions: Type[BaseException],
                   to_chain_class: Literal[False] = False) -> Iterator[M_co]:
        pass

    def filter_map(self,
                   function: Callable[[T_co], M_co],
                   *exceptions: Type[BaseException],
                   to_chain_class: bool = True) -> Union[Iterator[M_co], 'ChainIterator[M_co]']:
        """
        Creates an iterator that both filters and maps.
        The 'function' will be called to each value and if the 'exception' is not raised the iterator yield the result.

        Args:
            function:        function to map
            *exceptions:     exception to catch
            to_chain_class:  type of return value.
                            `Chained` generator if True, built-in 'generator' if False
        Returns:
            resulting iterator
        """
        mapper = filter_map(function, self, *exceptions)
        if to_chain_class:
            return ChainIterator(mapper)
        return mapper

    @overload
    def cmap(self,
             *predicates: Callable[[Any], T],
             to_chain_class: Literal[True] = True) -> 'ChainIterator[T]':
        pass

    @overload
    def cmap(self,
             *predicates: Callable[[Any], T],
             to_chain_class: Literal[False] = False) -> Iterator[T]:
        pass

    def cmap(self,
             *predicates: Callable[[Any], T],
             to_chain_class: bool = True) -> Union[Iterator[T], 'ChainIterator[T]']:
        """
        A composite analogue of the built-in function 'map' that allows the user to specify multiple mapping functions.
        They are executed sequentially from left to right.

        Args:
            *predicates:     functions to map
            to_chain_class:  type of return value.
                            `Chained` generator if True, built-in 'generator' if False
        Returns:
            resulting iterator
        """
        mapper = compose_map(self, *predicates)
        if to_chain_class:
            return ChainIterator(mapper)
        return mapper

    @overload
    def cfilter(self,
                *predicates: Callable[[Any], Any],
                to_chain_class: Literal[True] = True) -> 'ChainIterator[T_co]':
        pass

    @overload
    def cfilter(self,
                *predicates: Callable[[Any], Any],
                to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def cfilter(self,
                *predicates: Callable[[Any], Any],
                to_chain_class: bool = True) -> Union[Iterator[T_co], 'ChainIterator[T_co]']:
        """
        A composite analogue of the built-in function 'filter'
        that allows the user to specify multiple filter functions.
        They are executed lazily and sequentially from left to right.

        Args:
            *predicates:     filters to map
            to_chain_class:  type of return value.
                            `Chained` generator if True, built-in 'generator' if False
        Returns:
            resulting iterator
        """
        mapper = compose_filter(self, *predicates)
        if to_chain_class:
            return ChainIterator(mapper)
        return mapper

    @overload
    def multiarg_cmap(self,
                      *predicates: Callable[..., T],
                      to_chain_class: Literal[True] = True) -> 'ChainIterator[T]':
        pass

    @overload
    def multiarg_cmap(self,
                      *predicates: Callable[..., T],
                      to_chain_class: Literal[False] = False) -> Iterator[T]:
        pass

    def multiarg_cmap(self,
                      *predicates: Callable[..., T],
                      to_chain_class: bool = True) -> Union[Iterator[T], 'ChainIterator[T]']:
        """
        'compose_map' analogue that accepts multi-argument functions.

        These functions should return either a single value or a tuple of values.
        In the latter case, the returned tuple will be unpacked into the next function,
        but not passed as a single argument.

        Args:
            *predicates:     functions to map
            to_chain_class:  type of return value.
                            `Chained` generator if True, built-in 'generator' if False
        Returns:
            resulting generator
        """
        mapper = compose_multiarg_map(self, *predicates)
        if to_chain_class:
            return ChainIterator(mapper)
        return mapper

    @overload
    def multiarg_cfilter(self,
                         *predicates: Callable,
                         to_chain_class: Literal[True] = True) -> 'ChainIterator[T_co]':
        pass

    @overload
    def multiarg_cfilter(self,
                         *predicates: Callable,
                         to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def multiarg_cfilter(self,
                         *predicates: Callable,
                         to_chain_class: bool = True) -> Union[Iterator[T_co], 'ChainIterator[T_co]']:
        """
        'compose_filter' analogue that accepts multi-argument functions.

        These functions should return either a single value or a tuple of values.
        In the latter case, the returned tuple won't be passed as a single argument to the next function,
        but will be unpacked into it.

        Passes only those values that are transformed to True (maybe implicitly)
        by the 'compose_multiarg_map' with the same arguments.

        Args:
            predicates*:     functions to map
            to_chain_class:  type of return value.
                             `Chained` generator if True, built-in 'generator' if False
        Returns:
            resulting iterator
        """
        mapper = compose_multiarg_filter(self, *predicates)
        if to_chain_class:
            return ChainIterator(mapper)
        return mapper

    @overload
    def collect(self,  # type: ignore
                collector: Type[Iterable[T_co]],
                *,
                to_chain_class: Literal[False] = False) -> Iterable[T_co]:
        pass

    @overload
    def collect(self,
                collector: Type[Iterable[T_co]],
                *,
                to_chain_class: Literal[True] = True) -> 'AbstractChainIterable[T_co]':
        pass

    @overload
    def collect(self,
                collector: 'Type[AbstractChainIterable[T_co]]',
                *,
                to_chain_class: bool = True) -> 'AbstractChainIterable[T_co]':
        pass

    def collect(self,
                collector: Union[Type[Iterable[T_co]],
                                 'Type[AbstractChainIterable[T_co]]'],
                *,
                to_chain_class: bool = True) -> Union[Iterable[T_co], 'AbstractChainIterable[T_co]']:

        if to_chain_class:
            collector = make_chain_class(collector)
        return collector(self)  # type: ignore

    def run(self) -> None:
        """
        Evaluates the entire iterable and forgets about it.

        Returns:
            None
        """
        # Feeds the entire iterator of the corresponding iterable into a zero-length deque
        # https://docs.python.org/3/library/itertools.html#itertools-recipes
        deque(self, 0)

    @overload
    def transpose(self: 'AbstractChainIterable[Iterable[M_co]]',
                  to_chain_class: Literal[True] = True) -> 'ChainZip[M_co]':
        pass

    @overload
    def transpose(self: 'AbstractChainIterable[Iterable[M_co]]',
                  to_chain_class: Literal[False] = False) -> Iterator[Tuple[M_co, ...]]:
        pass

    def transpose(self: 'AbstractChainIterable[Iterable[M_co]]',
                  to_chain_class: bool = True) -> Union['ChainZip[M_co]', Iterator[Tuple[M_co, ...]]]:
        """
        Transposes the iterable if it iterates over other iterables.
        Be careful: The first-order iterable will be evaluated.

        Args:
            to_chain_class:  type of return value.
                            `Chained` zip iterator if True, built-in 'zip' if False.
                             Default is True.
        Returns:
            zip iterator
        """
        if to_chain_class:
            return ChainZip(*self)
        return zip(*self)

    @overload
    def take(self, n: int, to_chain_class: Literal[True] = True) -> 'ISlice[T_co]':
        pass

    @overload
    def take(self, n: int, to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def take(self, n: int, to_chain_class: bool = True) -> Union['ISlice[T_co]', Iterator[T_co]]:
        """
        Returns first n items of the iterable as an iterator.

        Args:
            n:               number of items to return
            to_chain_class:  type of return value.
                            `Chained` islice iterator if True, built-in 'itertools.islice' if False
        Returns:
            islice iterator
        """
        if to_chain_class:
            return ISlice(self, n)
        return islice(self, n)

    @overload
    def skip(self, n: int, to_chain_class: Literal[True] = True) -> 'ISlice[T_co]':
        pass

    @overload
    def skip(self, n: int, to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def skip(self, n: int, to_chain_class: bool = True) -> Union['ISlice[T_co]', Iterator[T_co]]:
        """
        Creates an iterator that skips the first n elements.

        Args:
            n:               number of items to skip
            to_chain_class:  type of return value.
                            `Chained` islice iterator if True, built-in 'itertools.islice' if False
        Returns:
            islice iterator
        """
        iterator = iter(self)
        next(
            (ISlice if to_chain_class else islice)(iterator, n, n),  # type: ignore
            None
        )
        return iterator

    def len(self) -> int:
        """
        Evaluates the iterable, counting the number of iterations.

        Returns:
            The number of iterations
        """
        last_elem = deque(enumerate(self, 1), 1)
        if last_elem:
            return last_elem.pop()[0]
        return 0

    def last(self, default: Any = None) -> Optional[T_co]:
        """
        Evaluates the iterable, returning the last element.

        Args:
            default:  default value to return
        Returns:
            The last element if the iterable contains anything. 'default' - otherwise
        """
        last_elem = deque(self, 1)
        if last_elem:
            return last_elem.pop()
        return default

    def nth(self, n: int, default: Any = None):
        """
        Evaluates the iterable until the n-th element, returning it.

        Args:
            n:        order number
            default:  default value to return

        Returns:
            The n-th element if the iterable contains it. 'default' - otherwise
        """
        return next(islice(self, n, None), default)

    @overload
    def step_by(self, step: int, to_chain_class: Literal[True] = True) -> 'ISlice[T_co]':
        pass

    @overload
    def step_by(self, step: int, to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def step_by(self, step: int, to_chain_class: bool = True) -> Union['ISlice[T_co]', Iterator[T_co]]:
        """
        Returns every 'step'-th item of the iterable as an iterator.

        Args:
            step:            number of iterations to skip
            to_chain_class:  type of return value.
                            `Chained` islice iterator if True, built-in 'itertools.islice' if False
        Returns:
            islice iterator
        """
        if to_chain_class:
            return ISlice(self, None, None, step)
        return islice(self, None, None, step)

    @overload
    def chain(self: 'AbstractChainIterable[M_co]',
              *iterables: Iterable[M_co],
              to_chain_class: Literal[True] = True) -> 'Chain[M_co]':
        pass

    @overload
    def chain(self: 'AbstractChainIterable[M_co]',
              *iterables: Iterable[M_co],
              to_chain_class: Literal[False] = False) -> Iterator[M_co]:
        pass

    def chain(self: 'AbstractChainIterable[M_co]',
              *iterables: Iterable[M_co],
              to_chain_class: bool = True) -> Union['Chain[M_co]', Iterator[M_co]]:
        """
        Takes an arbitrary number of iterables and creates a new iterator over self and each input iterable.

        Args:
            *iterables:      iterables to "extend"
            to_chain_class:  type of return value.
                            `Chained` chain iterator if True, built-in 'itertools.chain' if False
        Returns:
            A new iterator which will first iterate over values from the 'self'
            and then over values from the iterables (sequentially from first to last)
        """
        if to_chain_class:
            return Chain(self, *iterables)
        return chain(self, *iterables)

    @overload
    def zip(self: 'AbstractChainIterable[M_co]',
            *iterables: Iterable[M_co],
            to_chain_class: Literal[True] = True) -> 'Chain[Tuple[M_co, ...]]':
        pass

    @overload
    def zip(self: 'AbstractChainIterable[M_co]',
            *iterables: Iterable[M_co],
            to_chain_class: Literal[False] = False) -> Iterator[Tuple[M_co, ...]]:
        pass

    def zip(self: 'AbstractChainIterable[M_co]',
            *iterables: Iterable[M_co],
            to_chain_class: bool = True) -> Union['ChainIterator[Tuple[M_co, ...]]', Iterator[Tuple[M_co, ...]]]:
        """
        Takes an arbitrary number of iterables and "zips up" the 'self' with them into a single iterator of tuples.

        Args:
            *iterables:      iterables to "zip up"
            to_chain_class:  type of return value.
                            `Chained` zip iterator if True, built-in 'itertools.chain' if False
        Returns:
            A new iterator that will iterate over other iterables,
            returning a tuple where the first element comes from the 'self',
            and the n-th element comes from the (n-1)-th iterable from the 'iterables'.
        """
        if to_chain_class:
            return ChainZip(self, *iterables)
        return zip(self, *iterables)

    def unpack(self, receiver: protocol.varArgCallable[T_co, T]) -> T:
        """
        Unpacks the iterable into specified receiver.

        Args:
            receiver:  receiver to unpack into. It can be callable or type object
        Returns:
            Result of receiver.__call__(*self)
        """
        return receiver(*self)

    @overload
    def flat(self,
             *,
             to_chain_class: Literal[True] = True) -> 'ChainIterator[T_co]':
        pass

    @overload
    def flat(self,
             *,
             to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def flat(self,
             *,
             to_chain_class: bool = True) -> Union[Iterator[T_co], 'ChainIterator[T_co]']:
        """
        Creates an iterator that flattens nested structure. Removes all levels of indirection.
        Does not work for flattening 'str' and 'bytes'.

        Args:
            to_chain_class:  type of return value.
                            `Chained` generator if True, built-in 'generator' if False
        Returns:
            resulting iterator
        """
        flatter = flat(self)
        if to_chain_class:
            return ChainIterator(flatter)
        return flatter

    def foreach(self, function: Callable[[T_co], Any]) -> None:
        """
        Calls a function for each argument, evaluation the 'self'.

        Args:
            function:  function to call
        Returns:
            None
        """
        deque(map(function, self), 0)

    @overload
    def enumerate(self,
                  init_value: int = 0,
                  *,
                  to_chain_class: Literal[True] = True) -> 'ChainIterator[Tuple[int, T_co]]':
        pass

    @overload
    def enumerate(self,
                  init_value: int = 0,
                  *,
                  to_chain_class: Literal[False] = False) -> Iterator[Tuple[int, T_co]]:
        pass

    def enumerate(self,
                  init_value: int = 0,
                  *,
                  to_chain_class: bool = True) -> Union['ChainIterator[Tuple[int, T_co]]',
                                                        Iterator[Tuple[int, T_co]]]:
        """
        Creates an iterator which gives the current iteration count as well as the next value.

        Args:
            init_value:      initial value to count from
            to_chain_class:  type of return value.
                            `Chained` generator if True, built-in 'enumerate' if False
        Returns:
            resulting iterator
        """
        enumerator = enumerate(self, init_value)
        if to_chain_class:
            return ChainIterator(enumerator)
        return enumerator

    def inspect(self, callback: Callable[[T_co], Any]) -> 'ChainMap[T_co, T_co]':
        """
        Does something with each element of an iterable, passing the value on.

        Args:
            callback:  function to call
        Returns:
            resulting iterator
        """

        def f(x):
            callback(x)
            return x

        return ChainMap(f, self)


class AbstractChainIterator(AbstractChainIterable[T_co]):
    @abstractmethod
    def __next__(self) -> T_co: pass

    @abstractmethod
    def __iter__(self) -> 'Iterator[T_co]': pass


class ChainIterator(AbstractChainIterator[T_co]):
    def __init__(self, iterable: Iterable[T_co]) -> None:
        self._iterator: Final = iter(iterable)

    def __next__(self) -> T_co:
        return next(self._iterator)

    def __iter__(self) -> 'Iterator[T_co]':  # type: ignore
        return iter(self._iterator)

    @property
    def raw(self) -> Iterator[T_co]:
        return self._iterator

    def iter(self) -> 'ChainIterator[T_co]':
        return self

    @overload  # type: ignore
    def skip(self,
             n: int,
             to_chain_class: Literal[True] = True) -> 'ChainIterator[T_co]':
        pass

    @overload
    def skip(self,
             n: int,
             to_chain_class: Literal[False] = False) -> Iterator[T_co]:
        pass

    def skip(self,
             n: int,
             to_chain_class: bool = True) -> Union['ChainIterator[T_co]', Iterator[T_co]]:
        next(islice(self._iterator, n, n), None)
        if to_chain_class:
            return self
        return self._iterator


class ChainGenerator(AbstractChainIterator[T_co], Generic[T_co, T_contra, M_co]):
    def __init__(self, generator: Generator[T_co, T_contra, M_co]) -> None:
        if not isinstance(generator, GeneratorType):
            if isinstance(generator, ChainGenerator):
                generator = generator.raw
            else:
                raise TypeError(
                    f'{self.__class__.__name__} does not accept non-generator instances of {type(generator)}'
                )

        self._generator: Final[Generator[T_co, T_contra, M_co]] = generator

    def send(self, value: T_contra) -> T_co:
        return self._generator.send(value)

    def throw(self,
              exception: Type[BaseException],
              value: Any = None,
              traceback: Optional[TracebackType] = None) -> Any:
        return self._generator.throw(exception, value, traceback)

    def __repr__(self) -> str:
        return 'ChainGenerator'

    def __iter__(self) -> Iterator[T_co]:
        return iter(self._generator)

    def __next__(self) -> T_co:
        return next(self._generator)

    def close(self) -> None:
        self._generator.close()

    @property
    def gi_code(self) -> CodeType:
        return self._generator.gi_code

    @property
    def gi_frame(self) -> FrameType:
        return self._generator.gi_frame

    @property
    def gi_running(self) -> bool:
        return self._generator.gi_running

    @property
    def gi_yieldfrom(self) -> Optional[Generator]:
        return self._generator.gi_yieldfrom

    @property
    def raw(self) -> Generator[T_co, T_contra, M_co]:
        """
        Returns:
            Raw generator inside the 'self' instance
        """
        return self._generator


class ChainRange(Sequence[int], AbstractChainIterable[int]):
    def __init__(self, *args: Union[int, range]) -> None:
        try:
            self._range: range = range(*args)  # type: ignore
        except TypeError:
            if len(args) == 1 and isinstance(range_candidate := args[0], range):
                self._range: range = range_candidate  # type: ignore
            else:
                raise

    @overload
    def __getitem__(self, key: int) -> int:
        pass

    @overload
    def __getitem__(self, key: slice) -> 'ChainRange':
        pass

    def __getitem__(self, key: Union[int, slice]) -> Union[int, 'ChainRange']:
        if isinstance(key, slice):
            _range = self._range[key]
            if getrefcount(self) == 3:  # WARNING. Is it safe?
                self._range = _range
                return self
            return ChainRange(_range.start, _range.stop, _range.step)
        return self._range[key]

    def __len__(self) -> int:
        return len(self._range)

    def __repr__(self) -> str:
        return f'ChainRange({self._range.__repr__()[6:-1]})'

    def __iter__(self) -> Iterator[int]:
        return iter(self._range)

    @property
    def raw(self) -> range:
        """
        Returns:
            Raw 'range' object inside the 'self' instance
        """
        return self._range


class ChainMap(map,  # type: ignore
               protocol.Map[T_co, M_co],
               AbstractChainIterable[T_co]):
    def __repr__(self) -> str:
        return 'ChainMap'


class ChainFilter(filter,  # type: ignore
                  protocol.Filter[T_co],
                  AbstractChainIterable[T_co]):
    def __repr__(self) -> str:
        return 'ChainFilter'


class ChainZip(zip,  # type: ignore
               protocol.Zip[T_co],
               AbstractChainIterable[Tuple[T_co, ...]]):
    def __repr__(self) -> str:
        return 'ChainZip'


class ChainTuple(tuple, AbstractChainIterable[T]):
    pass


class ChainList(list, AbstractChainIterable[T]):
    pass


class ISlice(islice,  # type: ignore
             protocol.Islice[T],
             AbstractChainIterator[T]):
    def __iter__(self) -> 'ISlice[T]':
        return self


class Chain(chain,
            protocol.Chain[T],
            AbstractChainIterator[T]):
    def __iter__(self) -> 'Chain[T]':
        return self


# Cache dict for storing already created class - to - chain-class associations
_registered_chain_classes: Final[Dict] = {
    GeneratorType: ChainGenerator,
    range: ChainRange,
    map: ChainMap,
    filter: ChainFilter,
    zip: ChainZip,
    tuple: ChainTuple,
    list: ChainList,
    islice: ISlice,
    chain: Chain
}


def make_chain_class(cls: Type[Iterable[T]]) -> Type[AbstractChainIterable[T]]:
    """
    Makes a chained version of the iterable input class.

    Args:
        cls:  input class
    Returns:
        chained version of 'cls'
    """
    if issubclass(cls, AbstractChainIterable):
        return cls
    try:
        return _registered_chain_classes[cls]
    except KeyError:
        if not issubclass(cls, abc.Iterable):
            raise TypeError('A chain class can only be created from an iterable type')

    class Extended(cls, AbstractChainIterable[T_co]):  # type: ignore
        pass

    base_name = cls.__name__
    Extended.__name__ = Extended.__qualname__ = f'Chain{base_name[0].upper()}{base_name[1:]}'

    _registered_chain_classes[cls] = Extended
    return Extended


def make_chain(iterable: Iterable[T]) -> AbstractChainIterable[T]:
    """
    Makes a chaned version of the input iterable object.

    --------------------- Attention! ---------------------
    Behaves correctly only
    > for types already registered as keys in the '_registered_chain_classes'
    > or in the case if the `type(iterable)` can be a constructor for the iterable, i.e.
    if `type(iterable).__call__(iterable) == iterable` is True.

    Args:
        iterable:  input iterable object
    Returns:
        Chained version of this object
    """
    return make_chain_class(type(iterable))(iterable)
