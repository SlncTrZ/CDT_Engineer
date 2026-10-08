"""Regression tests for human-deliverable profile wiring and skill-depth adoption."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from execution.stage_runner import LOCAL_CAPABILITIES, run_profile

ROOT = Path(__file__).resolve().parents[1]


def _load_profile(domain: str) -> dict:
    return json.loads((ROOT / "domains" / domain / "agent-profile.json").read_text(encoding="utf-8"))


def _all_pass_inputs(profile: dict):
    local = {}
    by_sw = {}
    checks = {}
    deps = {}
    for stage in profile["stages"]:
        checks[stage["stage_id"]] = {"result": "pass"}
        candidates = stage.get("software_candidates", [])
        for semantic in stage.get("required_capabilities", []):
            if candidates and semantic not in LOCAL_CAPABILITIES:
                for sw in candidates:
                    by_sw.setdefault(sw, {})[semantic] = {"result": "pass"}
            else:
                local[semantic] = {"result": "pass"}
        if stage.get("dependency_requirements"):
            deps[stage["stage_id"]] = {
                req["dependency_id"]: {"state": "resolved"}
                for req in stage["dependency_requirements"]
            }
    return local, by_sw, checks, deps


def _deliverable_evidence(profile: dict, package_revision="pkg-1", source_revision="src-1"):
    evidence = {}
    for req in profile["human_deliverables"]["requirements"]:
        evidence[req["requirement_id"]] = {
            "applicability": "applicable",
            "implementation_state": "implemented",
            "verification_state": "verified",
            "acceptance_state": "pass",
            "reviewer": "reviewer-1",
            "reviewer_role": req["reviewer_role"],
            "independent": True,
            "evidence_refs": [f"evidence:{req['requirement_id']}"],
            "artifact_revision": package_revision,
            "source_revision": source_revision,
        }
    return evidence


class ProfileHumanDeliverableAdoptionTests(unittest.TestCase):
    def test_building_profile_fails_closed_without_human_deliverable_evidence(self):
        profile = _load_profile("building-architecture")
        self.assertIn("human_deliverables", profile)
        local, by_sw, checks, deps = _all_pass_inputs(profile)
        result = run_profile(
            profile,
            capabilities=local,
            capabilities_by_software=by_sw,
            stage_checks=checks,
            dependency_states=deps,
            package_revision="pkg-1",
            source_revision="src-1",
        )
        self.assertEqual("blocked", result["result"])
        target = profile["human_deliverables"]["stage_id"]
        stage = next(row for row in result["stages"] if row["stage_id"] == target)
        self.assertTrue(any(code.startswith("deliverable_evidence_missing:") for code in stage["assessment_reason_codes"]))

    def test_building_profile_passes_when_human_deliverable_hard_gates_pass(self):
        profile = _load_profile("building-architecture")
        local, by_sw, checks, deps = _all_pass_inputs(profile)
        result = run_profile(
            profile,
            capabilities=local,
            capabilities_by_software=by_sw,
            stage_checks=checks,
            dependency_states=deps,
            human_deliverable_evidence=_deliverable_evidence(profile),
            package_revision="pkg-1",
            source_revision="src-1",
        )
        self.assertEqual("pass", result["result"])
        self.assertEqual("pass", result["human_deliverables"]["result"])

    def test_mechanical_profile_is_second_real_consumer(self):
        profile = _load_profile("mechanical-reconstruction")
        self.assertIn("human_deliverables", profile)
        local, by_sw, checks, deps = _all_pass_inputs(profile)
        result = run_profile(
            profile,
            capabilities=local,
            capabilities_by_software=by_sw,
            stage_checks=checks,
            dependency_states=deps,
            human_deliverable_evidence=_deliverable_evidence(profile),
            package_revision="pkg-1",
            source_revision="src-1",
        )
        self.assertEqual("pass", result["human_deliverables"]["result"])


class SkillDepthAdoptionTests(unittest.TestCase):
    def test_site_and_mechanical_have_bounded_public_engineering_skill_packages(self):
        expectations = {
            "site-reconstruction": "site-registration-reconstruction",
            "mechanical-reconstruction": "mechanical-feature-reconstruction",
        }
        for domain, skill_id in expectations.items():
            base = ROOT / "domains" / domain / "skills" / skill_id
            for name in ("SKILL.md", "inputs.schema.json", "workflow.yaml"):
                self.assertTrue((base / name).is_file(), f"{domain}:{name}")
            text = (base / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"`skill_id`: `{skill_id}`", text)
            schema = json.loads((base / "inputs.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

    def test_site_and_mechanical_profiles_require_the_new_skills(self):
        expected = {
            "site-reconstruction": "domain.skill.site-registration-reconstruction",
            "mechanical-reconstruction": "domain.skill.mechanical-feature-reconstruction",
        }
        for domain, dependency_id in expected.items():
            profile = _load_profile(domain)
            ids = {
                req["dependency_id"]
                for stage in profile["stages"]
                for req in stage.get("dependency_requirements", [])
            }
            self.assertIn(dependency_id, ids)


if __name__ == "__main__":
    unittest.main()
