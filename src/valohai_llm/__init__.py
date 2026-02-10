from .logging import configure_logging
from .post import post_result
from .task import get_current_task

__version__ = "0.1.0"
__all__ = [
    "get_current_task",
    "post_result",
]

configure_logging()
