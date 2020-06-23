from functools import partial
from keyword import iskeyword
from typing import Any, Tuple, Final, MutableSet, Callable


def replace_call_with_eval_lambda(self, *args, **kwargs):
    """LambdaExpr.__call__ monkey patcher"""
    return self.eval_lambda()(*args, **kwargs)


class LambdaExpr:
    __slots__ = (
        '_tokens',
        '_lambda'
    )

    def __init__(self, *tokens: str) -> None:
        self._tokens: Final[Tuple[str, ...]] = tokens
        self._lambda: Callable = partial(replace_call_with_eval_lambda, self)
        # When __call__ is being invoked first time
        # it is replaced with 'eval_lambda' from the 'replace_call_with_eval_lambda' function above

    def __call__(self, *args, **kwargs):
        return self._lambda(*args, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self}' at {hex(id(self))}>"

    def __str__(self):
        return ''.join(map(str, self._tokens))

    def __getattr__(self, name: str) -> 'LambdaExpr':
        """
        Emulates something like ``lambda x: x.attr``
        using ``x.attr``, where ``x`` was defined as ``x = LambdaVar('x')``.

        Args:
            name:  name of an attribute
        Returns:
            Corresponding lambda-expression
        """
        return LambdaExpr(*self._tokens, '.', name)

    def get_args(self):
        return sorted(set(self._tokens) & _registered_vars)

    def eval_lambda(self) -> Callable:
        self._lambda = eval(
            f'lambda {",".join(self.get_args())}:{"".join(self._tokens)}'
        )
        return self._lambda

    def collapse(self, right: Any, *inter_tokens: str) -> 'LambdaExpr':
        if isinstance(right, LambdaExpr):
            return LambdaExpr(*self._tokens, *inter_tokens, *right._tokens)
        return LambdaExpr(*self._tokens, *inter_tokens, right)

    def __matmul__(self, other):
        return self.collapse(other, '@')

    def __sub__(self, other):
        return self.collapse(other, '-')


_registered_vars: Final[MutableSet[str]] = set()


class LambdaVar(LambdaExpr):
    """
    >>> tuple(map(LambdaVar('x') - LambdaVar('y'), (10, 20, 30), (10, 20, 20)))
    (0, 0, 10)
    """

    __slots__ = ()

    def __init__(self, name: str) -> None:

        if name in _registered_vars:
            raise NameError("")  # TODO
        if not name.isidentifier() or iskeyword(name):
            raise NameError("")  # TODO

        _registered_vars.add(name)
        super().__init__(name)

    def __str__(self):
        return self._tokens[0]


class LambdaArgs(LambdaVar):
    __slots__ = ()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LambdaArgs, cls).__new__(cls)
            cls.instance._tokens = ('*args',)
            _registered_vars.add('*args')
        return cls.instance

    def __init__(self):
        pass


class LambdaKwargs(LambdaVar):
    __slots__ = ()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LambdaKwargs, cls).__new__(cls)
            cls.instance._tokens = ('**kwargs',)
            _registered_vars.add('**kwargs')
        return cls.instance

    def __init__(self):
        pass

# args_ = LambdaVar('args')
# kwargs_ = LambdaVar('kwargs')
#
# sArgs = LambdaArgs()
#sKwargs = LambdaKwargs()
# x = LambdaVar('x')
# y = LambdaVar('y')
#
# x @ y

# (
#     (x @ y @ z @ sArgs @ sKwargs)
#     [x * 3 - y / 6]
# )

# f'sum({x} * 3) - sum({y} / 6)'
