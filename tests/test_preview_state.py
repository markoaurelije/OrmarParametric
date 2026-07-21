import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "commands"
    / "commandDialog"
    / "preview_state.py"
)
SPEC = importlib.util.spec_from_file_location("preview_state", MODULE_PATH)
preview_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preview_state)


class PreviewSessionStateTests(unittest.TestCase):
    def setUp(self):
        self.state = preview_state.PreviewSessionState()

    def test_staged_edits_wait_for_explicit_update(self):
        self.state.mark_dirty("O1_")

        self.assertEqual(set(), self.state.preview_prefixes())
        self.assertEqual({"O1_"}, self.state.execute_prefixes())

    def test_live_preview_returns_only_dirty_prefixes(self):
        self.state.live_preview = True
        self.state.mark_dirty("O2_")
        self.state.mark_dirty("O2_")

        self.assertEqual({"O2_"}, self.state.preview_prefixes())

    def test_enabling_live_preview_does_not_flush_older_staged_edits(self):
        self.state.mark_dirty("J1_")
        self.state.live_preview = True
        self.state.mark_dirty("O2_")

        self.assertEqual({"O2_"}, self.state.preview_prefixes())
        self.assertEqual({"J1_", "O2_"}, self.state.execute_prefixes())

    def test_explicit_update_works_when_live_preview_is_off(self):
        self.state.mark_dirty("J1_")
        self.state.request_update("J1_")

        self.assertEqual({"J1_"}, self.state.preview_prefixes())

    def test_successful_preview_clears_pending_but_keeps_execute_safety_net(self):
        self.state.live_preview = True
        self.state.mark_dirty("J1_")
        self.state.mark_preview_succeeded({"J1_"})

        self.assertEqual(set(), self.state.preview_prefixes())
        self.assertEqual({"J1_"}, self.state.execute_prefixes())

    def test_failed_prefix_remains_pending_for_retry(self):
        self.state.live_preview = True
        self.state.mark_dirty("J1_")
        self.state.mark_dirty("O1_")
        self.state.mark_preview_succeeded({"J1_"})

        self.assertEqual({"O1_"}, self.state.preview_prefixes())

    def test_reset_discards_all_session_state(self):
        self.state.live_preview = True
        self.state.request_update("J1_")
        self.state.reset()

        self.assertFalse(self.state.live_preview)
        self.assertEqual(set(), self.state.preview_prefixes())
        self.assertEqual(set(), self.state.execute_prefixes())

    def test_discard_removes_deleted_cabinet_from_all_work(self):
        self.state.live_preview = True
        self.state.request_update("J1_")
        self.state.discard({"J1_"})

        self.assertEqual(set(), self.state.preview_prefixes())
        self.assertEqual(set(), self.state.execute_prefixes())


class CabinetPrefixTests(unittest.TestCase):
    def test_matches_longest_parameter_suffix(self):
        self.assertEqual(
            "O2_",
            preview_state.cabinet_prefix(
                "O2_fronta_desna", ["fronta", "fronta_desna"]
            ),
        )

    def test_ignores_project_controls(self):
        self.assertIsNone(
            preview_state.cabinet_prefix(
                "finish_active_decor", ["fronta", "sirina"]
            )
        )

    def test_requires_prefix_separator(self):
        self.assertIsNone(preview_state.cabinet_prefix("sirina", ["sirina"]))


if __name__ == "__main__":
    unittest.main()