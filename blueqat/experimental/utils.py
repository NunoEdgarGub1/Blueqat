from keyword import iskeyword
from functools import wraps, update_wrapper
from typing import Tuple, Dict, Any, Callable, Union, Optional
from dataclasses import dataclass, field

from blueqat import Circuit, BlueqatGlobalSetting
from . import Ops
from .operations import MacroWrapper

def def_macro(func, name: str = None, allow_overwrite: bool = False):
    """Decorator for define and register a macro"""
    if name is None:
        if isinstance(func, str):
            # Decorator with arguments
            name = func
            def _wrapper(func):
                BlueqatGlobalSetting.register_macro(name, func, allow_overwrite)
                return func
            return _wrapper
        if callable(func):
            # Direct call or decorator without arguments
            name = func.__name__
            if not name.isidentifier() or iskeyword(name):
                raise ValueError('Invalid function name')
            BlueqatGlobalSetting.register_macro(name, func, allow_overwrite)
            return func
    if isinstance(name, str) and callable(func):
        BlueqatGlobalSetting.register_macro(name, func)
        return func
    raise ValueError('Invalid argument')


def targetable(func, call='never'):
    """Decorator to create gate-like class

    call: 'never', 'must', 'optional'
    """
    @dataclass
    class Inner:
        circuit: Union[Circuit, Ops]
        args: Tuple[Any] = ()
        kwargs: Dict[str, Any] = field(default_factory=dict)
        called: bool = False

        def __call__(self, *args, **kwargs):
            if call == 'never':
                raise AttributeError(func.__name__, 'is not callable.')
            if self.called:
                raise ValueError('Already called.')
            self.args = args
            self.kwargs = kwargs
            self.called = True
            return self

        def __getitem__(self, item):
            if self.circuit is None:
                raise ValueError('No circuit.')
            if call == 'must' and not self.called:
                raise ValueError('Not called.')
            return func(self.circuit, item, *self.args, **self.kwargs)

    class Wrapper(MacroWrapper):
        def __call__(self, *args, **kwargs):
            return Inner(*args, **kwargs)

    w = Wrapper()
    update_wrapper(w, func)
    return w
