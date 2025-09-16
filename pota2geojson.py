#!/usr/bin/env python3
"""
Convert a POTA entities JSON file into a GeoJSON FeatureCollection, with an
optional state filter.

- Input is expected to be a JSON array of entity dicts (e.g., from us-pota.json).
- Every input entity becomes a GeoJSON Feature.
- All original key/value pairs are preserved under 'properties'.
- geometry is a Point from (longitude, latitude) when both are present and valid.
  Otherwise, geometry is null (valid per RFC 7946) so no entities are lost.

Examples:
  # Entire dataset
  python pota2geojson.py /path/to/us-pota.json /path/to/output.geojson

  # Only California entities (accepts CA, us-ca, or US-CA)
  python pota2geojson.py /path/to/us-pota.json /path/to/ca.geojson --state CA
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Convert POTA entities JSON to GeoJSON FeatureCollection, with an optional state filter."
    )
    parser.add_argument(
        "input_json",
        type=Path,
        help="Path to the input us-pota.json file (array of entities).",
    )
    parser.add_argument(
        "output_geojson",
        type=Path,
        help="Path to write the resulting GeoJSON file.",
    )
    parser.add_argument(
        "--state",
        type=str,
        default=None,
        help="Optional state filter. Accepts 'CA', 'us-ca', or 'US-CA' and normalizes to 'US-CA'.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for output (default: 2).",
    )
    return parser.parse_args()


def load_entities(path: Path) -> list[dict[str, Any]]:
    """Load the JSON array of POTA entities from disk."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array of entities.")
    return data  # type: ignore[return-value]


def normalize_state_filter(state: str | None) -> str | None:
    """
    Normalize user-provided state text to 'US-XX' or return None if no filter.

    Accepted inputs:
      CA  -> US-CA
      ca  -> US-CA
      us-ca / US-CA -> US-CA
    """
    if not state:
        return None
    s = state.strip().upper()
    if s.startswith("US-"):
        return s  # already in US-XX
    if len(s) == 2:  # e.g., CA
        return f"US-{s}"
    if s.startswith("US_"):
        return "US-" + s[3:]
    if "-" in s:  # e.g., us-ca
        parts = s.split("-", 1)
        if len(parts[0]) == 2 and len(parts[1]) == 2:
            return f"{parts[0].upper()}-{parts[1].upper()}"
    return s  # fallback; caller compares literally


def _to_float(value: Any) -> float | None:
    """Best-effort conversion of a value to float; returns None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def make_feature(entity: dict[str, Any]) -> dict[str, Any]:
    """
    Build a GeoJSON Feature from a single entity.

    - Preserves all original keys in 'properties' (deep-copied).
    - Uses entity['longitude'] and entity['latitude'] for geometry when valid.
    """
    props = deepcopy(entity)

    lat = _to_float(entity.get("latitude"))
    lon = _to_float(entity.get("longitude"))

    geometry = {"type": "Point", "coordinates": [lon, lat]} if lat is not None and lon is not None else None

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": props,
    }


def to_feature_collection(entities: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert a list of entities to a GeoJSON FeatureCollection."""
    features = [make_feature(e) for e in entities]
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def main() -> None:
    """Entry point."""
    args = parse_args()
    want_state = normalize_state_filter(args.state)

    entities = load_entities(args.input_json)

    if want_state:
        entities = [e for e in entities if e.get("locationDesc") == want_state]

    fc = to_feature_collection(entities)

    args.output_geojson.parent.mkdir(parents=True, exist_ok=True)
    with args.output_geojson.open("w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=args.indent)

    total = len(fc["features"])
    with_coords = sum(1 for e in fc["features"] if e["geometry"] is not None)
    state_msg = f" for state {want_state}" if want_state else ""
    print(
        f"Wrote GeoJSON with {total} features{state_msg} to {args.output_geojson} "
        f"({with_coords} with coordinates, {total - with_coords} without)."
    )


if __name__ == "__main__":
    main()
