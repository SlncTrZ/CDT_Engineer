"""Regression cases for real progress instead of one-shot or fake reveals."""
import unittest
from execution.incremental_construction import assess_incremental_receipts

STAGES=["carcass", "first_door", "first_handle", "finish"]


def sample():
    return [
        {
            "stage_no": i+1,
            "stage_id": label,
            "root_cursor": i+1,
            "status": "verified_committed",
            "entities_added": (12 if i==0 else 1),
            "native_artifact_sha256": format(i+1, "064x"),
            "proof_image": f"native_frame_{i+1:02}.png",
        }
        for i,label in enumerate(STAGES)
    ]


class IncrementalEvidenceTests(unittest.TestCase):
    def test_real_chunk_receipts_pass(self):
        self.assertEqual("pass",assess_incremental_receipts(STAGES,sample())["result"])

    def test_backward_compatible_skp_hash_passes(self):
        rows = [
            {
                "stage_no": i+1,
                "stage_id": label,
                "root_cursor": i+1,
                "status": "verified_committed",
                "entities_added": (12 if i==0 else 1),
                "native_skp_sha256": format(i+1, "064x"),
                "proof_image": f"native_frame_{i+1:02}.png",
            }
            for i,label in enumerate(STAGES)
        ]
        self.assertEqual("pass", assess_incremental_receipts(STAGES, rows)["result"])

    def test_no_whole_model_stage_accepted(self):
        result=assess_incremental_receipts(["entire_cabinet"],[
            {"stage_no":1,"stage_id":"entire_cabinet","status":"verified_committed"}])
        self.assertEqual("blocked",result["result"])
        self.assertIn("insufficient_frozen_feature_plan",result["reason_codes"])

    def test_missing_stage_blocks(self):
        self.assertIn("stage_count_mismatch",assess_incremental_receipts(STAGES,sample()[:3])["reason_codes"])

    def test_skip_or_swap_blocks(self):
        rows=sample()
        rows[2]["stage_id"]="finish"
        self.assertEqual("blocked",assess_incremental_receipts(STAGES,rows)["result"])

    def test_faked_reveal_without_geometry_change_blocks(self):
        rows=sample()
        rows[2]["entities_added"]=0
        self.assertIn("no_new_entities:first_handle",assess_incremental_receipts(STAGES,rows)["reason_codes"])

    def test_reused_artifact_hash_blocks(self):
        rows=sample()
        rows[2]["native_artifact_sha256"]=rows[1]["native_artifact_sha256"]
        self.assertIn("unchanged_artifact_revision:first_handle",assess_incremental_receipts(STAGES,rows)["reason_codes"])

    def test_no_native_stage_image_blocks_visible_requirement(self):
        rows=sample()
        rows[2]["proof_image"]=""
        self.assertIn("missing_stage_visual_evidence:first_handle",assess_incremental_receipts(STAGES,rows)["reason_codes"])

    def test_headless_can_skip_screenshot_with_actual_chunks(self):
        rows=sample()
        rows[2]["proof_image"]=""
        self.assertEqual("pass",assess_incremental_receipts(STAGES,rows,visible_progress_required=False)["result"])

    def test_hidden_hinges_allow_identical_images_when_real_geometry_changes(self):
        rows=sample()
        rows[3]["proof_image"]=rows[2]["proof_image"]
        self.assertEqual("pass",assess_incremental_receipts(STAGES,rows)["result"])


if __name__=="__main__":
    unittest.main()
