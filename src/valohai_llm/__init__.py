from ._hooks import install_hooks as _install_hooks
from .post import collect_results, post_result
from .task import get_current_task

__version__ = "0.1.0"
__all__ = [
    "collect_results",
    "get_current_task",
    "post_result",
]

_install_hooks()
