from functools import partial
from keyword import iskeyword
from typing import Tuple, Final, MutableSet, Callable, Optional, Any, List

from chained.type_utils.meta import ChainedMeta


def _call_monkey_patcher(self, *args, **kwargs):
    """LambdaExpr.__call__ monkey patcher"""
    return self._eval()(*args, **kwargs)


class LambdaExpr(metaclass=ChainedMeta):
    """Implements functionality for shortened creation of lambda functions."""
    __slots__ = (
        '_tokens',
        '_lambda'
    )

    def __init__(self, *tokens: str) -> None:
        self._tokens: Final[Tuple[str, ...]] = tokens
        self._lambda: Callable = partial(_call_monkey_patcher, self)

    def __call__(self, *args, **kwargs):
        # When the object of type 'LambdaExpr' is called for the first time,
        # the class attribute '_lambda' is replaced with the one that evaluated by '_eval'.
        return self._lambda(*args, **kwargs)

    def __getattr__(self, name: str) -> 'LambdaExpr':
        """
        Emulates something like ``lambda x: x.attr``
        using ``x.attr``, where ``x`` was defined as ``x = LambdaVar('x')``.

        >>> x = LambdaVar('x')
        >>> tuple(map(x.real, (3, 4, 5 + 2j)))
        (3, 4, 5.0)

        Args:
            name:  name of an attribute
        Returns:
            Corresponding lambda-expression
        """
        return LambdaExpr('(', *self._tokens, ').', name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self}' at {hex(id(self))}>"

    def __str__(self) -> str:
        """
        >>> x = LambdaExpr('x')
        >>> y = LambdaExpr('y')
        >>> str(x - y)
        '(x)-y'

        Returns:
            string representation of the `LambdaExpr`
        """
        return ''.join(map(str, self._tokens))

    def _collapse(self, right: Any, *inter_tokens: str) -> 'LambdaExpr':
        if isinstance(right, LambdaExpr):
            return LambdaExpr(
                '(', *self._tokens, ')',
                *inter_tokens,
                *right._tokens
            )
        return LambdaExpr(
            '(', *self._tokens, ')',
            *inter_tokens,
            right
        )

    def _eval(self) -> Callable:
        """Evaluates tokens in a lambda function"""
        evaluated_lambda: Callable = eval(
            f'lambda {",".join(self._get_args())}:{"".join(self._tokens)}'
        )
        self._lambda = evaluated_lambda
        return evaluated_lambda

    def _get_args(self) -> List:
        return sorted(set(self._tokens) & _registered_vars)

    # >>> Unary operators
    def __pos__(self) -> 'LambdaExpr':
        return LambdaExpr('+(', *self._tokens, ')')

    def __neg__(self) -> 'LambdaExpr':
        return LambdaExpr('-(', *self._tokens, ')')

    def __invert__(self) -> 'LambdaExpr':
        return LambdaExpr('~(', *self._tokens, ')')

    def __abs__(self) -> 'LambdaExpr':
        return LambdaExpr('abs(', *self._tokens, ')')

    def __round__(self, n: Optional[int] = None) -> 'LambdaExpr':
        """
        >>> x = LambdaExpr('x')
        >>> tuple(map(round(x), (3.4, 44.334)))
        (3, 44)

        >>> tuple(map(round(x, 1), (3.4, 44.334)))
        (3.4, 44.3)

        Args:
            n:    precision
        Returns:
            rounded number
        """
        return LambdaExpr('round(', *self._tokens, f',{n})')

    # >>> Comparison methods
    def __eq__(self, other) -> 'LambdaExpr':  # type: ignore
        return self._collapse(other, '==')

    def __ne__(self, other) -> 'LambdaExpr':  # type: ignore
        return self._collapse(other, '!=')

    def __lt__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '<')

    def __gt__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '>')

    def __le__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '<=')

    def __ge__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '>=')

    # >>> Normal arithmetic operators
    def __add__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '+')

    def __sub__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '-')

    def __mul__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '*')

    def __floordiv__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '//')

    def __div__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '/')

    def __mod__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '%')

    def __divmod__(self, other) -> 'LambdaExpr':
        return LambdaExpr('divmod(', *self._tokens, ')')

    def __pow__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '**')

    def __matmul__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '@')

    def __lshift__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '<<')

    def __rshift__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '>>')

    def __and__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '&')

    def __or__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '|')

    def __xor__(self, other) -> 'LambdaExpr':
        return self._collapse(other, '^')

    # >>> Type conversion magic methods
    def __int__(self) -> 'LambdaExpr':
        return LambdaExpr('int(', *self._tokens, ')')

    def __float__(self) -> 'LambdaExpr':
        return LambdaExpr('float(', *self._tokens, ')')

    def __complex__(self) -> 'LambdaExpr':
        return LambdaExpr('complex(', *self._tokens, ')')

    def __oct__(self) -> 'LambdaExpr':
        return LambdaExpr('oct(', *self._tokens, ')')

    def __hex__(self) -> 'LambdaExpr':
        return LambdaExpr('hex(', *self._tokens, ')')

    # >>> Miscellaneous
    def __hash__(self) -> 'LambdaExpr':  # type: ignore
        return LambdaExpr('hash(', *self._tokens, ')')

    def __nonzero__(self) -> 'LambdaExpr':
        return LambdaExpr('bool(', *self._tokens, ')')

    # >>> Container methods
    def __len__(self) -> 'LambdaExpr':
        return LambdaExpr('len(', *self._tokens, ')')

    def __getitem__(self, key) -> 'LambdaExpr':
        return LambdaExpr('(', *self._tokens, f')[{key}]')

    def __setitem__(self, key, value) -> 'LambdaExpr':
        return LambdaExpr('(', *self._tokens, f')[{key}]={value}')

    def __delitem__(self, key) -> 'LambdaExpr':
        return LambdaExpr('del (', *self._tokens, f')[{key}]')

    def __iter__(self) -> 'LambdaExpr':
        return LambdaExpr('iter(', *self._tokens, ')')

    def __reversed__(self) -> 'LambdaExpr':
        return LambdaExpr('reversed(', *self._tokens, ')')

    def __contains__(self, item) -> 'LambdaExpr':
        return LambdaExpr(f'{item} in (', *self._tokens, ')')


_registered_vars: Final[MutableSet[str]] = set()


class LambdaVar(LambdaExpr):
    """
    >>> a = LambdaVar('a'); b = LambdaVar('b')
    >>> tuple(map(a - b, (10, 20, 30), (10, 20, 20)))
    (0, 0, 10)
    """

    __slots__ = ()

    def __init__(self, name: str) -> None:

        if name in _registered_vars:
            raise NameError(f'Name `{name}` has been already created')
        if not name.isidentifier() or iskeyword(name):
            raise NameError(f'Name `{name}` is not a valid identifier')

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
