# valohai-llm

[vh]: https://valohai.com/
[vh-llm]: https://llm.valohai.com/

Python instrumentation library for [Valohai][vh] large language model and generative AI tools.

## Installation

```shell
pip install valohai-llm

# `uv` project with pip-compatibility
uv pip install valohai-llm

# `uv`-managed project
uv add valohai-llm
```

## Usage

1. Get `VALOHAI_LLM_API_KEY` from [Valohai LLM][vh-llm]
2. Make sure `VALOHAI_LLM_API_KEY` is set in your environment
3. Use the library e.g. the simplest case:

```python
import valohai_llm

def main():
    result = valohai_llm.post_result(
        task="my-evaluation",
        labels={"model": "gpt-4", "dataset": "mmlu", "category": "math"},
        metrics={"accuracy": 0.85, "latency_ms": 150},
    )
    print("Result posted:", result)

if __name__ == "__main__":
    main()
```

## Development

```shell
# auto-format and lint code
just format

# run unit tests
uv run pytest

# configure setup to run examples
cp .env.dev-example .env
# edit the .env
uv run --env-file=.env --with-editable=. examples/simple_example.py
```
