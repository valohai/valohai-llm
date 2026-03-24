from __future__ import annotations

PROXY_BASE = "https://llm-proxy.example.com"
FAKE_COMPLETIONS_RESPONSE = {
    "id": "chatcmpl-fake",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "fake-model",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "hello"},
            "finish_reason": "stop",
        },
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}

FAKE_ANTHROPIC_RESPONSE = {
    "id": "msg-fake",
    "type": "message",
    "role": "assistant",
    "content": [{"type": "text", "text": "hello"}],
    "model": "fake-model",
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 1, "output_tokens": 1},
}
PROXY_CHAT_URL = f"{PROXY_BASE}/v1/chat/completions"
OTHER_CHAT_URL = "https://api.openai.com/v1/chat/completions"
