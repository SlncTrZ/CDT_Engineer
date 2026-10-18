"""Regression tests: visual polish and technical integrity are independently required."""
from pathlib import Path
import unittest

from execution.dual_quality_gate import assess_dual_quality_gate

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 64


def evidence(*, status="pass", artifact_sha256=SHA, views=True, independent=True):
    data = {
        "status": status,
        "artifact_sha256": artifact_sha256,
        "evidence_refs": ["native:reopen", "checker:assessment"],
        "reviewer": "checker-01",
        "reviewer_role": "discipline_checker",
        "independent": independent,
    }
    if views:
        data["view_types"] = ["overall", "front", "detail"]
    return data


class DualQualityGateTests(unittest.TestCase):
    def verify(self, technical=None, visual=None, **kwargs):
        return assess_dual_quality_gate(
            artifact_sha256=SHA,
            technical_gate=technical if technical is not None else evidence(),
            visual_gate=visual if visual is not None else evidence(),
            **kwargs,
        )

    def test_two_independently_passed_gates_release(self):
        got = self.verify()
        self.assertEqual(got["result"], "pass")
        self.assertEqual(got["technical_gate"], "pass")
        self.assertEqual(got["visual_gate"], "pass")

    def test_technical_pass_cannot_override_visual_fail(self):
        got = self.verify(visual=evidence(status="fail"))
        self.assertEqual(got["result"], "blocked")
        self.assertIn("visual_gate:fail", got["reason_codes"])

    def test_visual_pass_cannot_override_invalid_technical(self):
        got = self.verify(technical=evidence(status="fail"))
        self.assertEqual(got["result"], "blocked")
        self.assertIn("technical_gate:fail", got["reason_codes"])

    def test_unverified_visual_blocks(self):
        got = self.verify(visual=evidence(status="unknown"))
        self.assertIn("visual_gate:unknown", got["reason_codes"])

    def test_stale_visual_evidence_blocks(self):
        got = self.verify(visual=evidence(artifact_sha256="b" * 64))
        self.assertIn("visual_gate:artifact_revision_mismatch", got["reason_codes"])

    def test_missing_detail_view_blocks(self):
        got = self.verify(visual=evidence(views=False))
        self.assertIn("visual_gate:required_views_missing", got["reason_codes"])

    def test_custom_view_types_bind_purpose(self):
        v = evidence()
        v["view_types"] = ["sheet", "closeup"]
        result = self.verify(visual=v, required_visual_views=("sheet", "closeup"))
        self.assertEqual(result["result"], "pass")

    def test_missing_independent_review_blocks(self):
        got = self.verify(technical=evidence(independent=False))
        self.assertIn("technical_gate:independent_review_missing", got["reason_codes"])

    def test_missing_evidence_blocks(self):
        v = evidence()
        v["evidence_refs"] = []
        self.assertIn("visual_gate:evidence_missing", self.verify(visual=v)["reason_codes"])

    def test_missing_gate_blocks(self):
        got = assess_dual_quality_gate(artifact_sha256=SHA,technical_gate=evidence(),visual_gate=None)
        self.assertIn("visual_gate:missing", got["reason_codes"])

    def test_visual_na_cannot_bypass_actual_model(self):
        v = evidence(status="not_applicable")
        v.update(na_reason="No render requested", na_approved_by="reviewer")
        self.assertEqual(self.verify(visual=v)["result"], "blocked")

    def test_reviewer_approved_nonvisual_exception(self):
        v = evidence(status="not_applicable", views=False)
        v.update(na_reason="Machine-only numerical output", na_approved_by="technical_lead")
        got = self.verify(visual=v,visual_artifact=False)
        self.assertEqual(got["result"], "pass")

    def test_invalid_hash_blocks(self):
        got = assess_dual_quality_gate(artifact_sha256="not_sha",technical_gate=evidence(),visual_gate=evidence())
        self.assertIn("artifact_identity_missing_or_invalid", got["reason_codes"])

    def test_every_supported_software_guide_has_purpose_gate(self):
        for name in ("autocad", "sketchup", "blender", "solidworks"):
            guide = ROOT / "software" / name / "OPERATING_GUIDE.md"
            content = guide.read_text("utf-8")
            self.assertIn("dual quality policy", content, name)
            self.assertIn("technical_gate", content, name)
            self.assertIn("visual_gate", content, name)

    def test_normative_docs_link_dual_gate(self):
        for path in (
            "AGENTS.md",
            "docs/WORKFLOW_CONTRACT.md",
            "docs/ENGINEERING_SKILL_CONTRACT.md",
            "docs/QA_CHECKER_MODEL.md",
            "docs/SOFTWARE_OPERATING_GUIDE_CONTRACT.md",
        ):
            content = (ROOT / path).read_text("utf-8")
            self.assertIn("DUAL_QUALITY_GATE_POLICY.md", content, path)


if __name__ == "__main__":
    unittest.main()
