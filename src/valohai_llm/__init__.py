from ._hooks import install_hooks as _install_hooks
from ._state import state as _state_singleton
from .post import post_result
from .task import get_current_task

__version__ = "0.1.0"
__all__ = [
    "eval_scope",
    "finish_eval",
    "get_current_task",
    "post_result",
    "start_eval",
]

eval_scope = _state_singleton.eval_scope
start_eval = _state_singleton.start_eval
finish_eval = _state_singleton.finish_eval

_install_hooks()
