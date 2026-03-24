from __future__ import annotations

import os

API_KEY_ENVVAR = "VALOHAI_LLM_API_KEY"
LOG_LEVEL_ENVVAR = "VALOHAI_LLM_LOG"
NO_HOOKS_ENVVAR = "VALOHAI_LLM_NO_HOOKS"
NO_LANGFUSE_HOOK_ENVVAR = "VALOHAI_LLM_NO_LANGFUSE_HOOK"
NO_PROXY_HOOK_ENVVAR = "VALOHAI_LLM_NO_PROXY_HOOK"
PROXY_URL_ENVVAR = "VALOHAI_LLM_PROXY_URL"
URL_ENVVAR = "VALOHAI_LLM_URL"


def is_envvar_truthy(name: str) -> bool:
    val = os.environ.get(name)
    return val and val.lower() in ("true", "t", "1", "on", "yes")
