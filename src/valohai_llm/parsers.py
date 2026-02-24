"""Dataset file parsers."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path


class DatasetParseError(Exception):
    """Raised when a dataset file cannot be parsed."""


def default_items_from(path: Path) -> Iterable[dict]:
    """Parse dataset file based on extension.

    Supported formats:
    - .jsonl / .ndjson: JSON Lines (one JSON object per line)
    - .csv: CSV via csv.DictReader
    - .tsv: TSV via csv.DictReader with tab delimiter
    - .json: Single JSON array

    Args:
        path: Path to the dataset file.

    Yields:
        Parsed dict items from the dataset.

    Raises:
        DatasetParseError: If the file cannot be parsed.
    """
    suffix = path.suffix.lower()
    try:
        if suffix in (".jsonl", ".ndjson"):
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield json.loads(line)
        elif suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as f:
                yield from csv.DictReader(f)
        elif suffix == ".tsv":
            with path.open(encoding="utf-8", newline="") as f:
                yield from csv.DictReader(f, delimiter="\t")
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise DatasetParseError(f"Expected JSON array in {path}, got {type(data).__name__}")
            yield from data
        else:
            raise DatasetParseError(f"Unknown dataset format: {suffix}. Provide items_from=...")
    except DatasetParseError:
        raise
    except Exception as e:
        raise DatasetParseError(f"Failed to parse {path}: {e}") from e
