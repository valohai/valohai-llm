import logging
import os
import sys

from valohai_llm._config import (
    LOG_LEVEL_ENVVAR,
    NO_HOOKS_ENVVAR,
    NO_LANGFUSE_HOOK_ENVVAR,
    NO_PROXY_HOOK_ENVVAR,
    is_envvar_truthy,
)


def _configure_logging() -> None:
    """Configure logging for valohai_llm if VALOHAI_LLM_LOG is set to a valid level."""
    log_level_str = os.environ.get(LOG_LEVEL_ENVVAR, "").upper()
    if not log_level_str:
        return

    level = getattr(logging, log_level_str, None)
    if not isinstance(level, int):
        return

    logger = logging.getLogger("valohai_llm")
    logger.setLevel(level)

    handler: logging.Handler
    try:
        import rich.logging  # noqa: PLC0415 (late import on purpose)

        if sys.stderr.isatty():
            handler = rich.logging.RichHandler(rich_tracebacks=True)
        else:
            raise ImportError  # Fall through to standard handler
    except ImportError:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    handler.setLevel(level)
    logger.addHandler(handler)


def install_hooks() -> None:
    """Install hooks unless forbidden to."""
    if os.environ.get("PYTEST_VERSION"):  # Running in tests, do not hook implicitly
        return
    if is_envvar_truthy(NO_HOOKS_ENVVAR):
        return
    _configure_logging()
    if not is_envvar_truthy(NO_LANGFUSE_HOOK_ENVVAR):
        from ._langfuse import install_langfuse_hook  # noqa: PLC0415 – late import on purpose

        install_langfuse_hook()
    if not is_envvar_truthy(NO_PROXY_HOOK_ENVVAR):
        from ._proxy_hook import install_proxy_hook  # noqa: PLC0415 – late import on purpose

        install_proxy_hook()
