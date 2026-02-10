import logging
import os
import sys


def configure_logging() -> None:
    """Configure logging for valohai_llm if VALOHAI_LLM_LOG is set to a valid level."""
    log_level_str = os.environ.get("VALOHAI_LLM_LOG", "").upper()
    if not log_level_str:
        return

    level = getattr(logging, log_level_str, None)
    if not isinstance(level, int):
        return

    logger = logging.getLogger("valohai_llm")
    logger.setLevel(level)

    handler: logging.Handler
    try:
        import rich.logging

        if sys.stderr.isatty():
            handler = rich.logging.RichHandler(rich_tracebacks=True)
        else:
            raise ImportError  # Fall through to standard handler
    except ImportError:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    handler.setLevel(level)
    logger.addHandler(handler)
