"""CLI entry point: ``python -m valohai_llm.viewer <file> [--port PORT]``."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from valohai_llm.viewer._server import serve


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    results = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open() as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    raise ValueError("JSON file must contain a top-level array")


def _load_csv(path: Path) -> list[dict[str, Any]]:
    """Load CSV where columns are auto-classified as labels (string) or metrics (numeric)."""
    results = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels: dict[str, Any] = {}
            metrics: dict[str, Any] = {}
            for k, v in row.items():
                if k is None:
                    continue
                try:
                    metrics[k] = float(v)
                except (ValueError, TypeError):
                    labels[k] = v
            results.append({"labels": labels, "metrics": metrics})
    return results


def load_file(path: str) -> list[dict[str, Any]]:
    """Load results from a JSONL, JSON, or CSV file."""
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    suffix = p.suffix.lower()
    if suffix == ".jsonl":
        return _load_jsonl(p)
    if suffix == ".json":
        return _load_json(p)
    if suffix in (".csv", ".tsv"):
        return _load_csv(p)

    # Try JSONL first, fall back to JSON
    try:
        return _load_jsonl(p)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        return _load_json(p)
    except (json.JSONDecodeError, ValueError):
        pass
    print(f"Error: could not parse {path} as JSONL, JSON, or CSV", file=sys.stderr)  # noqa: T201
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m valohai_llm.viewer",
        description="Valohai LLM Results Viewer",
    )
    parser.add_argument("file", help="Results file (JSONL, JSON, or CSV)")
    parser.add_argument("--port", type=int, default=0, help="Port to serve on (0 = auto)")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    results = load_file(args.file)
    if not results:
        print("No results found in file.", file=sys.stderr)  # noqa: T201
        sys.exit(1)

    print(f"Loaded {len(results)} results from {args.file}")  # noqa: T201
    serve(results=results, port=args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()
