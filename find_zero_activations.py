#!/usr/bin/env python3
"""
Find POTA entities with no activations.

Reads a JSON file containing a list of POTA entities (dicts with keys like
"reference", "name", "activations", etc.) and prints those with zero activations.

Usage:
  python find_zero_activations.py /path/to/us-pota.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Find POTA entities with zero activations.")
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to the us-pota.json file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write matching entities as JSON.",
    )
    return parser.parse_args()


def load_entities(json_path: Path) -> list[dict]:
    """Load the JSON array of POTA entities from disk."""
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array of entities.")
    return data


def is_zero_activation(entity: dict) -> bool:
    """
    Return True if the entity has zero activations.

    Rules:
    - Missing field → zero
    - Null/None → zero
    - 0 (int or string) → zero
    - Anything else → not zero
    """
    activations = entity.get("activations")
    if activations is None:
        return True
    try:
        return int(activations) == 0
    except (TypeError, ValueError):
        return False


def main() -> None:
    """Entry point."""
    args = parse_args()
    entities = load_entities(args.json_path)

    zero_activation = [e for e in entities if is_zero_activation(e)]
    total = len(entities)
    count = len(zero_activation)

    # Pretty print to stdout
    print(f"Total entities: {total}")
    print(f"Entities with zero activations: {count}\n")
    for e in zero_activation:
        ref = str(e.get("reference", "UNKNOWN"))
        name = str(e.get("name", "Unnamed"))
        loc = str(e.get("locationDesc", ""))
        print(f"{ref}\t{name}\t{loc}")

    # Optional: write JSON output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(zero_activation, f, ensure_ascii=False, indent=2)
        print(f"\nWrote {count} entities to {args.output}")


if __name__ == "__main__":
    main()
