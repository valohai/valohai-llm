"""Results viewer for Valohai LLM evaluations.

Usage::

    from valohai_llm.viewer import serve
    serve(results=[...])

Or from the command line::

    python -m valohai_llm.viewer results.jsonl
"""

from __future__ import annotations

from valohai_llm.viewer._server import serve

__all__ = ["serve"]
