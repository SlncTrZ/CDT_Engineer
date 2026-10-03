"""Synthetic source evidence for tests only; never derive production inventory from output."""
from __future__ import annotations

import hashlib
import json

FAMILIES = {
    "axes": ("axes", "axis_id", None),
    "walls": ("walls", "wall_id", None),
    "bearing_walls": ("walls", "wall_id", ("wall_type", "bearing")),
    "partition_walls": ("walls", "wall_id", ("wall_type", "partition")),
    "columns": ("columns", "column_id", None),
    "doors": ("openings", "opening_id", ("opening_type", "door")),
    "windows": ("openings", "opening_id", ("opening_type", "window")),
    "spaces": ("spaces", "space_id", None),
    "fixtures": ("fixtures", "fixture_id", None),
    "dimensions": ("dimensions", "dimension_id", None),
}


def freeze_test_source(spec):
    """Freeze BEFORE a negative test removes/changes features."""
    payload = spec["payload"]
    items = []
    for family, (key, id_key, selector) in FAMILIES.items():
        refs = [v[id_key] for v in payload.get(key, [])
                if selector is None or v.get(selector[0]) == selector[1]]
        item = {"item_id": family, "semantic_family": family,
                "required": bool(refs), "feature_refs": refs,
                "evidence_state": "specified", "source_evidence": ["synthetic-test-source"]}
        if not refs:
            item.update(exclusion_reason="Not included in this bounded synthetic fixture.",
                        reviewed_by="test-checker")
        items.append(item)
    spec["source_inventory"] = {
        "source_id": "synthetic-test-source",
        "source_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "source_type": "specified", "review_passes": [], "items": items,
    }
    return spec
