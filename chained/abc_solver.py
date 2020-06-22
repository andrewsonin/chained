from collections import abc, deque, defaultdict
from typing import Final, Mapping, Type, Tuple, Dict

from chained.type_utils.typevar import T


def _get_abc_priority(hierarchical_graph: Mapping[Type[T], Tuple[Type[T], ...]]) -> Dict[Type[T], int]:
    """
    collections.abc priority builder. See '_abc_priority' below for clarity.

    Returns:
        ABC's priority mapping based on topological sorting
    Note:
        Not used in code. Only needed for reproducibility.
    """

    def topological_sort():
        visited = defaultdict(bool)
        stack = []

        def branch_visitor(vertex):
            visited[vertex] = True

            for i in hierarchical_graph[vertex]:
                if not visited[i]:
                    branch_visitor(i)

            stack.append(vertex)

        for cls in hierarchical_graph.keys():
            if not visited[cls]:
                branch_visitor(cls)

        return stack

    sorting_result = topological_sort()
    priorities = {
        cls: i
        for i, cls
        in enumerate(reversed(sorting_result))
    }
    keys = priorities.keys()
    priorities = {}
    for key in keys:
        priority = 0
        for base in key.__bases__:
            base_priority = priorities.get(base, -1)
            if base_priority >= priority:
                priority = base_priority + 1
        priorities[key] = priority
    return dict(sorted(priorities.items(), key=lambda x: x[1]))


_abc_hierarchy: Final = {
    abc.Container: (abc.Collection,),
    abc.Iterable: (abc.Iterator, abc.Reversible, abc.Collection),
    abc.Iterator: (abc.Generator,),
    abc.Reversible: (abc.Sequence,),
    abc.Generator: (),
    abc.Sized: (abc.Collection, abc.MappingView),
    abc.Collection: (abc.Sequence, abc.Set, abc.Mapping, abc.ValuesView),
    abc.Sequence: (abc.MutableSequence, abc.ByteString),
    abc.MutableSequence: (),
    abc.ByteString: (),
    abc.Set: (abc.MutableSet, abc.ItemsView, abc.KeysView),
    abc.MutableSet: (),
    abc.Mapping: (abc.MutableMapping,),
    abc.MutableMapping: (),
    abc.MappingView: (abc.ItemsView, abc.KeysView, abc.ValuesView),
    abc.ItemsView: (),
    abc.KeysView: (),
    abc.ValuesView: (),
    abc.Hashable: (),
    abc.Awaitable: (abc.Coroutine,),
    abc.Coroutine: (),
    abc.AsyncIterable: (abc.AsyncIterator,),
    abc.AsyncIterator: (abc.AsyncGenerator,),
    abc.AsyncGenerator: ()
}

_abc_priority: Final = {
    abc.AsyncIterable: 0,
    abc.Awaitable: 0,
    abc.Hashable: 0,
    abc.Sized: 0,
    abc.Iterable: 0,
    abc.Container: 0,
    abc.AsyncIterator: 1,
    abc.Coroutine: 1,
    abc.MappingView: 1,
    abc.Reversible: 1,
    abc.Iterator: 1,
    abc.Collection: 1,
    abc.AsyncGenerator: 2,
    abc.Generator: 2,
    abc.ValuesView: 2,
    abc.Mapping: 2,
    abc.Set: 2,
    abc.Sequence: 2,
    abc.MutableMapping: 3,
    abc.KeysView: 3,
    abc.ItemsView: 3,
    abc.MutableSet: 3,
    abc.ByteString: 3,
    abc.MutableSequence: 3
}  # To reproduce, run _get_abc_priority

_all_abcs: Final = {
    abc.AsyncGenerator,
    abc.AsyncIterable,
    abc.AsyncIterator,
    abc.Awaitable,
    abc.ByteString,
    abc.Collection,
    abc.Container,
    abc.Coroutine,
    abc.Generator,
    abc.Hashable,
    abc.ItemsView,
    abc.Iterable,
    abc.Iterator,
    abc.KeysView,
    abc.Mapping,
    abc.MappingView,
    abc.MutableMapping,
    abc.MutableSequence,
    abc.MutableSet,
    abc.Reversible,
    abc.Sequence,
    abc.Set,
    abc.Sized,
    abc.ValuesView
}


def resolve_abstract_bases(cls):
    """
    Finds abstract base classes from the 'collections.abc'
    for a collection type that most closely match its interface.

    Result is a dictionary with these ABCs as keys and their priorities* as values.

    *based on topological sorting of the hierarchical graph of their relationships

    Args:
        cls:  type to find ABCs for
    Returns:
        Resulting dict
    """
    matched_abcs = {}
    abcs_to_check = _all_abcs.copy()
    abcs_to_remove = deque(())

    while abcs_to_check:
        abc_candidate = abcs_to_check.pop()
        if issubclass(cls, abc_candidate):
            for matched_abc in tuple(matched_abcs.keys()):
                if issubclass(matched_abc, abc_candidate):
                    break
                if issubclass(abc_candidate, matched_abc):
                    matched_abcs.pop(matched_abc)
            else:
                matched_abcs[abc_candidate] = _abc_priority[abc_candidate]
            continue
        abcs_to_remove.extend(_abc_hierarchy[abc_candidate])
        while abcs_to_remove:
            abc_to_remove = abcs_to_remove.popleft()
            if abc_to_remove not in abcs_to_check:
                continue
            abcs_to_check.remove(abc_to_remove)
            abcs_to_remove.extend(_abc_hierarchy[abc_to_remove])
    return matched_abcs
