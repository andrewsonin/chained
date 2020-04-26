from collections import abc
from sys import getrefcount
from types import GeneratorType, TracebackType, new_class
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Union,
    Type,
    Optional,
    Generator,
    Sequence,
    Final,
    Literal,
    Tuple,
    Dict,

    overload
)

import lib.typing.protocol as protocol
from lib.functions import flat
from lib.functions.optimized import (
    compose_map,
    compose_filter,
    compose_multiarg_map,
    compose_multiarg_filter
)
from lib.typing.typevar import T, T_co, M_co, T_contra


class ChainIterable(protocol.singleArgInitIterable[T_co]):
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
        if to_chain_class:
            return ChainFilter(predicate, self)
        return filter(predicate, self)

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
                to_chain_class: Literal[True] = True) -> 'ChainIterable[T_co]':
        pass

    @overload
    def collect(self,
                collector: 'Type[ChainIterable[T_co]]',
                *,
                to_chain_class: bool = True) -> 'ChainIterable[T_co]':
        pass

    def collect(self,
                collector: Union[Type[Iterable[T_co]],
                                 'Type[ChainIterable[T_co]]'],
                *,
                to_chain_class: bool = True) -> Union[Iterable[T_co], 'ChainIterable[T_co]']:

        if to_chain_class:
            collector = make_chain_class(collector)
        return collector(self)  # type: ignore

    def run(self) -> None:
        for _ in self:
            pass

    @overload
    def transpose(self: 'ChainIterable[Iterable[M_co]]',
                  to_chain_class: Literal[True] = True) -> 'ChainZip[M_co]':
        pass

    @overload
    def transpose(self: 'ChainIterable[Iterable[M_co]]',
                  to_chain_class: Literal[False] = False) -> Iterator[Tuple[M_co, ...]]:
        pass

    def transpose(self: 'ChainIterable[Iterable[M_co]]',
                  to_chain_class: bool = True) -> Union['ChainZip[M_co]', Iterator[Tuple[M_co, ...]]]:
        if to_chain_class:
            return ChainZip(*self)
        return zip(*self)

    def unpack(self, receiver: protocol.varArgCallable[T_co, T]) -> T:
        return receiver(*self)

    @overload
    def flat(self,
             *,
             to_chain_class: Literal[True] = True) -> 'ChainGenerator[T_co, None, None]':
        pass

    @overload
    def flat(self,
             *,
             to_chain_class: Literal[False] = False) -> Generator[T_co, None, None]:
        pass

    def flat(self,
             *,
             to_chain_class: bool = True) -> Union[Generator[T_co, None, None], 'ChainGenerator[T_co, None, None]']:
        flatter = flat(self)
        if to_chain_class:
            return ChainGenerator(flatter)
        return flatter

    @overload
    def compose_map(self,
                    *predicates: Callable[[Any], T],
                    to_chain_class: Literal[True] = True) -> 'ChainGenerator[T, None, None]':
        pass

    @overload
    def compose_map(self,
                    *predicates: Callable[[Any], T],
                    to_chain_class: Literal[False] = False) -> Generator[T, None, None]:
        pass

    def compose_map(self,
                    *predicates: Callable[[Any], T],
                    to_chain_class: bool = True) -> Union[Generator[T, None, None],
                                                          'ChainGenerator[T, None, None]']:
        mapper = compose_map(self, *predicates)
        if to_chain_class:
            return ChainGenerator(mapper)
        return mapper

    @overload
    def compose_filter(self,
                       *predicates: Callable[[Any], Any],
                       to_chain_class: Literal[True] = True) -> 'ChainGenerator[T_co, None, None]':
        pass

    @overload
    def compose_filter(self,
                       *predicates: Callable[[Any], Any],
                       to_chain_class: Literal[False] = False) -> Generator[T_co, None, None]:
        pass

    def compose_filter(self,
                       *predicates: Callable[[Any], Any],
                       to_chain_class: bool = True) -> Union[Generator[T_co, None, None],
                                                             'ChainGenerator[T_co, None, None]']:
        mapper = compose_filter(self, *predicates)
        if to_chain_class:
            return ChainGenerator(mapper)
        return mapper

    @overload
    def compose_multiarg_map(self,
                             *predicates: Callable[..., T],
                             to_chain_class: Literal[True] = True) -> 'ChainGenerator[T, None, None]':
        pass

    @overload
    def compose_multiarg_map(self,
                             *predicates: Callable[..., T],
                             to_chain_class: Literal[False] = False) -> Generator[T, None, None]:
        pass

    def compose_multiarg_map(self,
                             *predicates: Callable[..., T],
                             to_chain_class: bool = True) -> Union[Generator[T, None, None],
                                                                   'ChainGenerator[T, None, None]']:
        mapper = compose_multiarg_map(self, *predicates)
        if to_chain_class:
            return ChainGenerator(mapper)
        return mapper

    @overload
    def compose_multiarg_filter(self,
                                *predicates: Callable,
                                to_chain_class: Literal[True] = True) -> 'ChainGenerator[T_co, None, None]':
        pass

    @overload
    def compose_multiarg_filter(self,
                                *predicates: Callable,
                                to_chain_class: Literal[False] = False) -> Generator[T_co, None, None]:
        pass

    def compose_multiarg_filter(self,
                                *predicates: Callable,
                                to_chain_class: bool = True) -> Union[Generator[T_co, None, None],
                                                                      'ChainGenerator[T_co, None, None]']:
        mapper = compose_multiarg_filter(self, *predicates)
        if to_chain_class:
            return ChainGenerator(mapper)
        return mapper


class ChainGenerator(Generator[T_co, T_contra, M_co], ChainIterable[T_co]):
    def __init__(self, generator: Generator[T_co, T_contra, M_co]) -> None:
        if not isinstance(generator, GeneratorType):
            raise TypeError(
                f'{self.__class__.__name__} does not accept non-generator instances of {type(generator)}'
            )

        self.generator: Final[Generator[T_co, T_contra, M_co]] = generator

    def send(self, value: T_contra) -> T_co:
        return self.generator.send(value)

    def throw(self,
              exception: Type[BaseException],
              value: Any = None,
              traceback: Optional[TracebackType] = None) -> Any:
        return self.generator.throw(exception, value, traceback)

    def __repr__(self) -> str:
        return 'ChainGenerator'

    def __iter__(self) -> Generator[T_co, T_contra, M_co]:
        return self.generator.__iter__()

    def __next__(self) -> T_co:
        return next(self.generator)

    def close(self) -> None:
        self.generator.close()


class ChainRange(Sequence[int], ChainIterable[int]):
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

    def raw_range(self) -> range:
        return self._range


class ChainMap(map,  # type: ignore
               protocol.MapProtocol[T_co, M_co],
               ChainIterable[T_co]):
    def __repr__(self) -> str:
        return 'ChainMap'


class ChainFilter(filter,  # type: ignore
                  protocol.FilterProtocol[T_co],
                  ChainIterable[T_co]):
    def __repr__(self) -> str:
        return 'ChainFilter'


class ChainZip(zip,  # type: ignore
               protocol.ZipProtocol[T_co],
               ChainIterable[Tuple[T_co, ...]]):
    def __repr__(self) -> str:
        return 'ChainZip'


_registered_chain_classes: Final[Dict] = {
    GeneratorType: ChainGenerator,
    range: ChainRange,
    map: ChainMap,
    filter: ChainFilter,
    zip: ChainZip
}


def make_chain_class(cls: Type[Iterable[T_co]]) -> Type[ChainIterable[T_co]]:
    if issubclass(cls, ChainIterable):
        return cls
    try:
        return _registered_chain_classes[cls]
    except KeyError:
        if not issubclass(cls, abc.Iterable):
            raise TypeError('A chain class can only be created from an iterable type')

    base_name = cls.__name__
    chain_cls = new_class(
        f'Chain{base_name[0].upper()}{base_name[1:]}',
        (cls, ChainIterable[T_co])
    )

    _registered_chain_classes[cls] = chain_cls
    return chain_cls


def make_chain(iterable: Iterable[T_co]) -> ChainIterable[T_co]:
    return make_chain_class(type(iterable))(iterable)


ChainTuple: Final = make_chain_class(tuple)
ChainList: Final = make_chain_class(list)
