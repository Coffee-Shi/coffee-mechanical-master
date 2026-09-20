from __future__ import annotations

import contextlib
import io
import json
import unittest

import fit_lookup


class FitLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tolerance_data = fit_lookup.load_json("standard-tolerances.json")
        cls.fit_data = fit_lookup.load_json("preferred-fits.json")

    def test_it_values_at_20_mm(self) -> None:
        self.assertEqual(fit_lookup.tolerance_width(20, "IT7", self.tolerance_data), 21)
        self.assertEqual(fit_lookup.tolerance_width(20, "IT6", self.tolerance_data), 13)

    def test_boundary_30_mm_is_lower_step(self) -> None:
        self.assertEqual(fit_lookup.tolerance_width(30, "IT7", self.tolerance_data), 21)
        self.assertEqual(fit_lookup.tolerance_width(30.001, "IT7", self.tolerance_data), 25)

    def test_precision_slide_match(self) -> None:
        family = fit_lookup.family_for_scene("低速不回转滑动，要求精密导向", self.fit_data["families"])
        self.assertIsNotNone(family)
        self.assertEqual(family["primary_fit"], "H7/g6")

    def test_ambiguous_scene_requires_disambiguation(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(
                [
                    "--diameter-mm", "20",
                    "--scene", "普通润滑油下的精密滑动",
                    "--connection", "moving",
                    "--motion", "轴向滑动",
                    "--precision", "high",
                    "--speed", "low",
                    "--load", "light",
                    "--lubrication", "oil",
                    "--temperature", "stable",
                    "--sealing", "none",
                ]
            )
        output = stream.getvalue()
        self.assertEqual(code, 3)
        self.assertIn("同时命中", output)
        self.assertNotIn("推荐标注", output)

    def test_generic_piston_refuses(self) -> None:
        family = fit_lookup.family_for_scene("有一个活塞要在缸体内运动", self.fit_data["families"])
        self.assertIsNone(family)

    def test_missing_diameter_asks_instead_of_recommending(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(["--scene", "精密滑动"])
        output = stream.getvalue()
        self.assertEqual(code, 3)
        self.assertIn("基本直径", output)
        self.assertNotIn("H7/g6", output)

    def test_partial_moving_scene_asks_for_operating_conditions(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(
                [
                    "--diameter-mm", "20",
                    "--scene", "精密滑动",
                    "--connection", "moving",
                    "--motion", "往复滑动",
                    "--precision", "high",
                ]
            )
        output = stream.getvalue()
        self.assertEqual(code, 3)
        self.assertIn("转速、线速度或往复频率", output)
        self.assertIn("润滑", output)
        self.assertNotIn("推荐标注", output)

    def test_generic_piston_asks_questions_not_fallback(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(
                [
                    "--diameter-mm", "20",
                    "--scene", "活塞在缸体内运动",
                    "--connection", "moving",
                    "--motion", "往复滑动",
                    "--precision", "high",
                ]
            )
        output = stream.getvalue()
        self.assertEqual(code, 3)
        self.assertIn("密封", output)
        self.assertNotEqual(output.strip(), fit_lookup.FALLBACK)

    def test_complete_precision_slide_matches(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(
                [
                    "--diameter-mm", "20",
                    "--scene", "低速精密滑动",
                    "--connection", "moving",
                    "--motion", "往复滑动",
                    "--precision", "high",
                    "--speed", "low",
                    "--load", "light",
                    "--lubrication", "oil",
                    "--temperature", "stable",
                    "--sealing", "由密封圈承担，圆柱面只导向",
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["status"], "matched")
        self.assertEqual(payload["information_gate"], "passed")
        self.assertEqual(payload["recommended_fit"], "H7/g6")

    def test_complete_unknown_scene_uses_exact_fallback(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(
                [
                    "--diameter-mm", "20",
                    "--scene", "知识库没有的磁悬浮运动",
                    "--connection", "moving",
                    "--motion", "连续旋转",
                    "--precision", "high",
                    "--speed", "high",
                    "--load", "light",
                    "--lubrication", "none",
                    "--temperature", "stable",
                    "--sealing", "none",
                ]
            )
        self.assertEqual(code, 2)
        self.assertEqual(stream.getvalue().strip(), fit_lookup.FALLBACK)

    def test_out_of_range_uses_exact_fallback(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(["--diameter-mm", "4000", "--scene", "精密滑动"])
        self.assertEqual(code, 2)
        self.assertEqual(stream.getvalue().strip(), fit_lookup.FALLBACK)

    def test_question_json_is_valid(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(["--scene", "精密滑动", "--json"])
        self.assertEqual(code, 3)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["status"], "need_more_information")
        self.assertTrue(payload["questions"])

    def test_large_size_rejects_unlisted_zone(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(["--diameter-mm", "600", "--fit", "H6/t5"])
        self.assertEqual(code, 2)
        self.assertEqual(stream.getvalue().strip(), fit_lookup.FALLBACK)

    def test_large_size_accepts_listed_zone(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(["--diameter-mm", "600", "--fit", "H7/u6", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stream.getvalue())["recommended_fit"], "H7/u6")

    def test_json_output_is_valid(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = fit_lookup.main(["--diameter-mm", "20", "--fit", "H7/g6", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["recommended_fit"], "H7/g6")
        self.assertEqual(payload["tolerance_widths"]["hole"]["um"], 21)
        self.assertEqual(payload["tolerance_widths"]["shaft"]["um"], 13)


if __name__ == "__main__":
    unittest.main()
