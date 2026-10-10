"""Offline semantic contract tests: no Blender runtime import or native dependencies."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "software/blender/OPERATING_GUIDE.md"
MAP = ROOT / "software/blender/engine-map.yaml"
CONTRACT = ROOT / "docs/BLENDER_MOTION_GRAPHICS_EXTENSION_CONTRACT.md"
EXPECTED_TOOLS = {
    "import_svg_curves",
    "create_grease_strokes",
    "create_filled_grease_tween",
    "create_particle_preset",
    "create_animated_particle_grid",
    "create_unicode_text",
    "create_shaped_text_plane",
}


def test_blender_extension_map_has_complete_unique_semantic_bindings():
    manifest = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    tools = [tool for item in manifest["capability_mappings"] for tool in item["public_tools"]]
    assert set(tools) == EXPECTED_TOOLS
    assert len(tools) == len(set(tools)) == 7
    assert all(item["source_status"] == "native_source_qualified" for item in manifest["capability_mappings"])


def test_source_qualification_does_not_claim_installed_gateway_or_blender5():
    snapshot = yaml.safe_load(MAP.read_text(encoding="utf-8"))["source_snapshot"]
    assert snapshot["contract_version"] == "cdt-blender-contract-v10"
    assert snapshot["public_tool_count_expected"] == 121
    assert snapshot["installed_gateway_e2e_qualified"] is False
    assert snapshot["other_blender_versions_qualified"] is False


def test_blender_public_guide_and_contract_have_distinct_doc_classes():
    assert "> Documentation class: PUBLIC_CONTRACT" in CONTRACT.read_text(encoding="utf-8")
    assert "> Documentation class: PUBLIC_SOFTWARE_GUIDE" in GUIDE.read_text(encoding="utf-8")


def test_raster_shaping_is_explicit_and_native_editable_text_is_not_claimed():
    docs = CONTRACT.read_text(encoding="utf-8") + GUIDE.read_text(encoding="utf-8")
    assert "RAQM" in docs and "HarfBuzz" in docs and "FriBidi" in docs
    assert "raster" in docs.lower()
    assert "not editable" in docs.lower()


def test_contract_covers_recovery_and_allow_roots():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "allow-roots" in text
    assert "reconcile_operation" in text
    assert "op_id" in text
    assert "atomic transaction" in text
