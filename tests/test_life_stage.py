import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc_logic.life_stage import determine_group


class LifeStageTests(unittest.TestCase):
    def test_single_50s_uses_fallback_group(self):
        group_id, fallback_note = determine_group(55, "single", 0, "none")
        self.assertEqual(group_id, 2)
        self.assertTrue(fallback_note)

    def test_married_40s_with_teen_child_maps_to_group_6(self):
        group_id, fallback_note = determine_group(45, "married", 1, "middle_high")
        self.assertEqual(group_id, 6)
        self.assertEqual(fallback_note, "")


if __name__ == "__main__":
    unittest.main()
