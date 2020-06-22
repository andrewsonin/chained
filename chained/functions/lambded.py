from functools import partial
from keyword import iskeyword
from typing import Any, Tuple, Final, MutableSet


def replace_call_with_eval_lambda(self, *args, **kwargs):
    """LambdaExpr.__call__ monkey patcher"""
    return self.eval_lambda()(*args, **kwargs)


class LambdaExpr:
    def __init__(self, *tokens: Any) -> None:
        self.tokens: Tuple = tokens
        self.lambda_func = partial(replace_call_with_eval_lambda, self)
        # When __call__ is being invoked first time
        # it is replaced with 'eval_lambda' from the 'replace_call_with_eval_lambda' function above

    @property
    def __call__(self):
        return self.lambda_func

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self}' at {hex(id(self))}>"

    def __str__(self):
        return ''.join(map(str, self.tokens))

    def get_args(self):
        return sorted(set(self.tokens) & _registered_vars)

    def eval_lambda(self):
        self.lambda_func = eval(
            f'lambda {",".join(self.get_args())}:{"".join(map(str, self.tokens))}'
        )
        return self.lambda_func

    def collapse(self, right: Any, *inter_tokens: str) -> 'LambdaExpr':
        if isinstance(right, LambdaExpr):
            return LambdaExpr(*self.tokens, *inter_tokens, *right.tokens)
        return LambdaExpr(*self.tokens, *inter_tokens, right)

    def __matmul__(self, other):
        return self.collapse(other, '@')

    def __sub__(self, other):
        return self.collapse(other, '-')


_registered_vars: Final[MutableSet[str]] = set()


class LambdaVar(LambdaExpr):
    def __init__(self, name: str) -> None:

        if name in _registered_vars:
            raise NameError("")  # TODO
        if not name.isidentifier() or iskeyword(name):
            raise NameError("")  # TODO

        _registered_vars.add(name)
        super().__init__(name)

    def __str__(self):
        return self.tokens[0]


class LambdaArgs(LambdaVar):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LambdaArgs, cls).__new__(cls)
            cls.instance.tokens = ('*args',)
            _registered_vars.add('*args')
        return cls.instance

    def __init__(self):
        pass


class LambdaKwargs(LambdaVar):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LambdaKwargs, cls).__new__(cls)
            cls.instance.tokens = ('**kwargs',)
            _registered_vars.add('**kwargs')
        return cls.instance

    def __init__(self):
        pass


# args_ = LambdaVar('args')
# kwargs_ = LambdaVar('kwargs')
#
# sArgs = LambdaArgs()
# sKwargs = LambdaKwargs()
# x = LambdaVar('x')
# y = LambdaVar('y')
#
# x @ y

# (
#     (x @ y @ z @ sArgs @ sKwargs)
#     [x * 3 - y / 6]
# )

# f'sum({x} * 3) - sum({y} / 6)'
