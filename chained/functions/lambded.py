from functools import partial
from keyword import iskeyword
from typing import Tuple, Final, Callable, Any, List, Generator, NoReturn, Dict

from chained.type_utils.meta import ChainedMeta


def _call_monkey_patcher(self, *args, **kwargs):
    """LambdaExpr.__call__ monkey patcher"""
    return self.eval()(*args, **kwargs)


def _token_expander(value: Any) -> Generator[Any, None, None]:
    """Expands tokens from an instance of ``LambdaExpr``. Otherwise - yields single 'value'.

    >>> x = LambdaExpr('x', '+', 'y')
    >>> tuple(_token_expander(x))
    ('x', '+', 'y')

    >>> tuple(_token_expander('value'))
    ('value',)

    Args:
        value:  token or `LambdaExpr` to expand
    Returns:
        resulting generator
    """
    if isinstance(value, LambdaExpr):
        yield from value._tokens
    else:
        yield value


class LambdaExpr(metaclass=ChainedMeta):
    """Implements functionality for shortened creation of lambda functions."""
    __slots__ = (
        '_tokens',
        '_lambda',
        '_string_repr'
    )

    def __init__(self, *tokens: Any) -> None:
        self._tokens: Final[Tuple[Any, ...]] = tokens
        self._lambda: Callable = partial(_call_monkey_patcher, self)

    def __call__(self, *args, **kwargs):
        # When the object of type 'LambdaExpr' is called for the first time,
        # the class attribute '_lambda' is replaced with the one that evaluated by the 'eval' method.
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
            Corresponding lambda expression
        """
        return LambdaExpr('(', *self._tokens, f').{name}')

    def __repr__(self) -> str:
        """
        >>> x = LambdaVar('x')
        >>> y = LambdaVar('y')
        >>> (x - y).__repr__()[:35]
        '<LambdaExpr(lambda x,y:(x)-(y)) at '

        Returns:
            __repr__ of the `LambdaExpr`
        """
        try:
            string_repr = self.__getattribute__('_string_repr')
        except AttributeError:
            self.eval()
            string_repr = self._string_repr
        return f'<{self.__class__.__name__}({string_repr}) at {hex(id(self))}>'

    def __str__(self) -> str:
        """
        >>> x = LambdaVar('x')
        >>> y = LambdaVar('y')
        >>> str(x - y)
        '(x)-(y)'

        Returns:
            string representation of the `LambdaExpr`
        """

        def tok_filter():
            for tok in map(str, self._tokens):
                if tok[0] != '*' or len(tok) < 3:  # Normal variable, or "*", or "**"
                    yield tok
                elif tok[1] != '*':
                    yield tok[1:]  # *args
                else:
                    yield tok[2:]  # **kwargs

        return ''.join(tok_filter())

    def _(self, *args, **kwargs) -> 'LambdaExpr':
        """
        Emulates ``__call__`` inside ``LambdaExpr``.

        >>> x = LambdaExpr('x')
        >>> str(x._('4', 'a', k='23', www='32'))
        '(x)((4),(a),k=(23),www=(32),)'

        >>> x = LambdaExpr('x')
        >>> str(x._('4', "'a'", k='23', www='32'))
        "(x)((4),('a'),k=(23),www=(32),)"

        >>> str(x._(k='23', www='32'))
        '(x)(k=(23),www=(32),)'

        >>> str(x._('4', 'a'))
        '(x)((4),(a),)'

        >>> str(x._('4'))
        '(x)((4),)'

        >>> str(x._(kwarg='kw'))
        '(x)(kwarg=(kw),)'

        >>> str(x._())
        '(x)()'

        Args:
            *args:     positional arguments to pass
            **kwargs:  keyword arguments to pass
        Returns:
            lambda expression
        """

        def args_tokenizer() -> Generator[Any, None, None]:
            for arg in args:
                yield '('
                yield from _token_expander(arg)
                yield '),'

        def kwargs_tokenizer() -> Generator[Any, None, None]:
            for k, v in kwargs.items():
                yield f'{k}=('
                yield from _token_expander(v)
                yield '),'

        return LambdaExpr(
            '(', *self._tokens, ')(',
            *args_tokenizer(),
            *kwargs_tokenizer(),
            ')'
        )

    def _collapse(self, inter_token: str, right: 'LambdaExpr') -> 'LambdaExpr':
        """Collapses 'self' with 'right' so that they are both evaluated before the effect of 'inter_token'

        >>> x = LambdaExpr('x')
        >>> y = LambdaExpr('y')
        >>> z = LambdaExpr('z')
        >>> str(x._collapse('*', y + z))
        '(x)*((y)+(z))'

        Args:
            inter_token:  middle token
            right:        instance of `LambdaExpr` to the right
        Returns:
            resulting `LambdaExpr`
        """
        if isinstance(right, LambdaExpr):
            return LambdaExpr(
                '(', *self._tokens, ')',
                inter_token,
                '(', *right._tokens, ')'
            )
        return LambdaExpr(
            '(', *self._tokens, ')',
            inter_token,
            '(', right, ')'
        )

    def _get_args(self) -> List:
        """Returns an argument list of a future lambda function built on the ``LambdaExpr``.

        Returns:
            argument list
        """

        arg_set = set(self._tokens) & _registered_vars.keys()

        starred_args = []
        if (args := '*args') in arg_set:
            arg_set.remove(args)
            starred_args.append(args)
        if (kwargs := '**kwargs') in arg_set:
            arg_set.remove(kwargs)
            starred_args.append(kwargs)

        arg_list = sorted(arg_set)
        arg_list += starred_args

        return arg_list

    def eval(self) -> Callable:
        """Evaluates tokens into a lambda function.

        >>> x = LambdaVar('x')
        >>> y = LambdaVar('y')
        >>> func = (x * y - 3 + 1).eval()
        >>> func(3, 4)
        10

        >>> func(2, 2)
        2
        """
        string_repr = f'lambda {",".join(self._get_args())}:{self}'
        self._string_repr: str = string_repr
        evaluated_lambda = eval(string_repr)
        self._lambda = evaluated_lambda
        return evaluated_lambda

    # >>> Unary operators
    def __pos__(self) -> 'LambdaExpr':
        return LambdaExpr('+(', *self._tokens, ')')

    def __neg__(self) -> 'LambdaExpr':
        return LambdaExpr('-(', *self._tokens, ')')

    def __invert__(self) -> 'LambdaExpr':
        return LambdaExpr('~(', *self._tokens, ')')

    def __abs__(self) -> 'LambdaExpr':
        return LambdaExpr('abs(', *self._tokens, ')')

    def __round__(self, n=None) -> 'LambdaExpr':
        """
        >>> x = LambdaVar('x')
        >>> tuple(map(round(x), (3.4, 44.334)))
        (3, 44)

        >>> tuple(map(round(x, 1), (3.4, 44.334)))
        (3.4, 44.3)

        Args:
            n:    precision
        Returns:
            rounded number
        """
        n = n._tokens if isinstance(n, LambdaExpr) else (n,)
        return LambdaExpr('round(', *self._tokens, ',', *n, ')')

    # >>> Comparison methods
    def __eq__(self, other) -> 'LambdaExpr':  # type: ignore
        """
        >>> str(LambdaExpr('x') == LambdaExpr('y'))
        '(x)==(y)'
        """
        return self._collapse('==', other)

    def __ne__(self, other) -> 'LambdaExpr':  # type: ignore
        return self._collapse('!=', other)

    def __lt__(self, other) -> 'LambdaExpr':
        return self._collapse('<', other)

    def __gt__(self, other) -> 'LambdaExpr':
        return self._collapse('>', other)

    def __le__(self, other) -> 'LambdaExpr':
        return self._collapse('<=', other)

    def __ge__(self, other) -> 'LambdaExpr':
        return self._collapse('>=', other)

    # >>> Normal arithmetic operators
    def __add__(self, other) -> 'LambdaExpr':
        return self._collapse('+', other)

    def __sub__(self, other) -> 'LambdaExpr':
        return self._collapse('-', other)

    def __mul__(self, other) -> 'LambdaExpr':
        return self._collapse('*', other)

    def __floordiv__(self, other) -> 'LambdaExpr':
        return self._collapse('//', other)

    def __truediv__(self, other) -> 'LambdaExpr':
        return self._collapse('/', other)

    def __mod__(self, other) -> 'LambdaExpr':
        return self._collapse('%', other)

    def __divmod__(self, other) -> 'LambdaExpr':
        return LambdaExpr('divmod(', *self._tokens, ')')

    def __pow__(self, other) -> 'LambdaExpr':
        return self._collapse('**', other)

    def __matmul__(self, other) -> 'LambdaExpr':
        return self._collapse('@', other)

    def __lshift__(self, other) -> 'LambdaExpr':
        return self._collapse('<<', other)

    def __rshift__(self, other) -> 'LambdaExpr':
        return self._collapse('>>', other)

    def __and__(self, other) -> 'LambdaExpr':
        return self._collapse('&', other)

    def __or__(self, other) -> 'LambdaExpr':
        return self._collapse('|', other)

    def __xor__(self, other) -> 'LambdaExpr':
        return self._collapse('^', other)

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
        return LambdaExpr('(', *self._tokens, ')[', key, ']')

    def __setitem__(self, key, value) -> 'LambdaExpr':
        return LambdaExpr('(', *self._tokens, ')[', key, ']=(', value, ')')

    def __delitem__(self, key) -> 'LambdaExpr':
        return LambdaExpr('del (', *self._tokens, ')[', key, ']')

    def __iter__(self) -> 'LambdaExpr':
        return LambdaExpr('iter(', *self._tokens, ')')

    def __reversed__(self) -> 'LambdaExpr':
        return LambdaExpr('reversed(', *self._tokens, ')')

    def __contains__(self, item) -> 'LambdaExpr':
        return LambdaExpr('(', item, ') in (', *self._tokens, ')')

    # >>> Keyword substitutes
    def _if(self, cond, /) -> 'LambdaExpr':
        cond = cond._tokens if isinstance(cond, LambdaExpr) else (cond,)
        return LambdaExpr('(', *self._tokens, ') if (', *cond, ')')

    def _else(self, alt, /) -> 'LambdaExpr':
        alt = alt._tokens if isinstance(alt, LambdaExpr) else (alt,)
        return LambdaExpr(*self._tokens, ' else (', *alt, ')')

    def _for(self, item, /):
        item = item._tokens if isinstance(item, LambdaExpr) else (item,)
        return LambdaExpr('(', *self._tokens, ') for (', *item, ')')

    def _in(self, item, /):
        item = item._tokens if isinstance(item, LambdaExpr) else (item,)
        return LambdaExpr(*self._tokens, ' in (', *item, ')')


class _LambdaVarMeta(ChainedMeta):
    __slots__ = ()

    def __call__(cls, name: str):  # type: ignore
        instance = _registered_vars.get(name, None)
        if instance is not None:
            return instance
        if not name.isidentifier() or iskeyword(name):
            raise NameError(f'LambdaVar with name `{name}` is not a valid identifier')
        return super().__call__(name)


class LambdaVar(LambdaExpr, metaclass=_LambdaVarMeta):
    """
    >>> a = LambdaVar('a')
    >>> b = LambdaVar('b')
    >>> tuple(map(a - b, (10, 20, 30), (10, 20, 20)))
    (0, 0, 10)
    """

    __slots__ = ()

    def __new__(cls, name: str) -> 'LambdaVar':
        return super().__new__(cls)

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._string_repr = name
        _registered_vars[name] = self


class _StarredLambdaVarMeta(_LambdaVarMeta):
    __slots__ = ()

    def __call__(cls):
        return cls.__new__(cls)


class _StarredLambdaVar(LambdaVar, metaclass=_StarredLambdaVarMeta):
    """Special abstract ``LambdaVar`` handler for ``*args`` and ``**kwargs``."""
    __slots__ = ()

    def __new__(cls, name: str):
        instance = _registered_vars.get(name, None)
        if instance is not None:
            return instance
        instance = LambdaExpr.__new__(cls)
        instance._string_repr = name
        _registered_vars[name] = instance
        return instance

    def __call__(self, *args, **kwargs) -> NoReturn:
        raise TypeError(
            f'Cannot build a lambda function based only on the starred `LambdaVar` instance {repr(self)}'
        )

    def __iter__(self) -> Generator[str, None, None]:  # type: ignore
        pass


class LambdaArgs(_StarredLambdaVar):
    __slots__ = ()

    def __new__(cls) -> 'LambdaArgs':
        return super().__new__(LambdaArgs, '*args')

    def __iter__(self) -> Generator[str, None, None]:  # type: ignore
        yield 'args'


class LambdaKwargs(_StarredLambdaVar):
    __slots__ = ()

    def __new__(cls) -> 'LambdaKwargs':
        return super().__new__(LambdaKwargs, '**kwargs')

    def __iter__(self) -> Generator[str, None, None]:  # type: ignore
        yield 'kwargs'


_registered_vars: Final[Dict[str, LambdaVar]] = {}

x = LambdaVar('x')
y = LambdaVar('y')
z = LambdaVar('z')
