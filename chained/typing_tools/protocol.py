from typing import Protocol, Iterable, Callable, Iterator, Tuple, Optional

from chained.typing_tools.typevar import T_co, M_co, T_contra


class varArgCallable(Protocol[T_contra, T_co]):
    def __call__(self, *args: T_contra) -> T_co: pass


class singleArgInitializable(Protocol[T_co]):
    def __init__(self, arg: Iterable[T_co]) -> None: pass


class Map(Protocol[T_co, M_co]):
    def __init__(self, predicate: Callable[[T_contra], M_co], iterable: Iterable[T_contra]) -> None: pass


class Filter(Protocol[T_co]):
    def __init__(self, predicate: Callable[[T_co], bool], iterable: Iterable[T_co]) -> None: pass


class Zip(Protocol[T_co]):
    def __init__(self, *args: Iterable[T_co]) -> None: pass

    def __iter__(self) -> Iterator[Tuple[T_co, ...]]: pass

    def __next__(self) -> Tuple[T_co, ...]: pass


class Islice(Protocol[T_co]):
    def __init__(self,
                 iterable: Iterable[T_co],
                 start: Optional[int],
                 stop: Optional[int] = None,
                 step: Optional[int] = None): pass


class Chain(Protocol[T_co]):
    def __init__(self, *iterables: Iterable[T_co]): pass
