from typing import Protocol

from chained.type_utils.typevar import T_co, T_contra


class varArgCallable(Protocol[T_contra, T_co]):
    def __call__(self, *args: T_contra) -> T_co:
        pass
