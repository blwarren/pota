#!/usr/bin/env python3
"""
Find the least activated POTA parks in California (locationDesc = "US-CA").

Reads a JSON file of POTA entities and prints those with the fewest activations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Find least activated POTA parks in California.")
    parser.add_argument(
        "json_path",
        type=Path,
        help="Path to the us-pota.json file.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="How many parks to show (default: 20).",
    )
    return parser.parse_args()


def load_entities(json_path: Path) -> list[dict]:
    """Load the JSON array of POTA entities from disk."""
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array of entities.")
    return data


def get_activation_count(entity: dict) -> int:
    """Safely convert the 'activations' field to an int, treating null/None/'' as zero."""
    activations = entity.get("activations", 0)
    if activations is None or activations == "":
        return 0
    try:
        return int(activations)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    """Entry point."""
    args = parse_args()
    entities = load_entities(args.json_path)

    # Filter for California
    ca_entities = [e for e in entities if e.get("locationDesc") == "US-CA"]

    # Attach activation counts
    ca_with_counts = [(get_activation_count(e), e) for e in ca_entities]

    # Sort by activations ascending
    ca_with_counts.sort(key=lambda x: x[0])

    # Display results
    print(f"Found {len(ca_entities)} California parks.")
    print(f"Showing {min(args.limit, len(ca_with_counts))} with the fewest activations:\n")

    for count, e in ca_with_counts[: args.limit]:
        ref = e.get("reference", "UNKNOWN")
        name = e.get("name", "Unnamed")
        print(f"{ref}\t{count}\t{name}")


if __name__ == "__main__":
    main()
