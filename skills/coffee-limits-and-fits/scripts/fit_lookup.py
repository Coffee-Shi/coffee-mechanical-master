#!/usr/bin/env python3
"""Deterministic, knowledge-base-only fit recommender and IT width lookup."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_ROOT / "references" / "data"
FALLBACK = "未在知识库中找到合适的公差配合，是否让人工智能自己思考。"
FIT_RE = re.compile(r"^([A-Z]+)(\d+)/(js|[a-z]+)(\d+)$")

# GB/T 1801—1999 来源页列明的 >500–3150 mm 常用公差带。
LARGE_HOLE_ZONES = {
    "G6", "H6", "JS6", "K6", "M6", "N6",
    "F7", "G7", "H7", "JS7", "K7", "M7", "N7",
    "D8", "E8", "F8", "H8", "JS8",
    "D9", "E9", "F9", "H9", "JS9",
    "D10", "H10", "JS10", "D11", "H11", "JS11", "H12", "JS12",
}
LARGE_SHAFT_ZONES = {
    "g6", "h6", "js6", "k6", "m6", "n6", "p6", "r6", "s6", "t6", "u6",
    "f7", "g7", "h7", "js7", "k7", "m7", "n7", "p7", "r7", "s7", "t7", "u7",
    "d8", "e8", "f8", "h8", "js8",
    "d9", "e9", "f9", "h9", "js9",
    "d10", "h10", "js10", "d11", "h11", "js11", "h12", "js12",
}

# 只在多个已命中场景之间消解优先级；不会使未命中的场景获得分数。
SCENARIO_PRIORITY = {
    "extra_heavy_press": 100,
    "heavy_press": 95,
    "medium_press": 90,
    "light_press": 88,
    "standard_press": 86,
    "high_temperature_running": 84,
    "tight_transition": 80,
    "medium_transition": 78,
    "light_transition": 76,
    "loose_transition": 74,
    "precision_sliding": 72,
    "precision_location_clearance": 68,
    "loose_location_clearance": 66,
    "large_clearance_running": 64,
    "loose_running": 62,
    "very_loose_running": 60,
    "normal_running": 50,
}


def load_json(name: str) -> dict[str, Any]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def tolerance_row(diameter_mm: float, data: dict[str, Any]) -> dict[str, Any] | None:
    if diameter_mm <= 0:
        return None
    for row in data["rows"]:
        if row["over_mm"] < diameter_mm <= row["through_mm"]:
            return row
    return None


def tolerance_width(diameter_mm: float, grade: str, data: dict[str, Any]) -> float | None:
    row = tolerance_row(diameter_mm, data)
    if row is None:
        return None
    return row["values_um"].get(grade)


def parse_fit(fit: str) -> tuple[str, int, str, int] | None:
    match = FIT_RE.fullmatch(fit.strip())
    if not match:
        return None
    return match.group(1), int(match.group(2)), match.group(3), int(match.group(4))


def family_for_fit(fit: str, families: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized = fit.strip()
    for family in families:
        if normalized == family["primary_fit"] or normalized in family["alternatives"]:
            return family
    return None


def family_for_scene(scene: str, families: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized = "".join(scene.lower().split())
    ranked: list[tuple[int, int, int, dict[str, Any]]] = []
    for family in families:
        hits = [keyword for keyword in family["keywords"] if "".join(keyword.lower().split()) in normalized]
        if not hits:
            continue
        ranked.append(
            (
                SCENARIO_PRIORITY.get(family["id"], 0),
                len(hits),
                sum(len(value) for value in hits),
                family,
            )
        )
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[:3], reverse=True)
    if len(ranked) > 1 and ranked[0][:3] == ranked[1][:3]:
        return None
    return ranked[0][3]


def process_candidates(surface: str, grade_number: int, process_data: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for process in process_data["processes"]:
        if process["surface"] != surface:
            continue
        if not process["it_min"] <= grade_number <= process["it_max"]:
            continue
        relative_cost = None
        for tier in process["cost_tiers"]:
            if tier["it_min"] <= grade_number <= tier["it_max"]:
                relative_cost = tier["relative_cost"]
                break
        result.append(
            {
                "method": process["name"],
                "capability": f"IT{process['it_min']}–IT{process['it_max']}",
                "relative_cost": relative_cost,
                "cost_reference": process["cost_reference"],
            }
        )
    result.sort(key=lambda item: (item["relative_cost"] is None, item["relative_cost"] or 99, item["method"]))
    return result


def make_result(diameter_mm: float, family: dict[str, Any], fit: str) -> dict[str, Any] | None:
    parsed = parse_fit(fit)
    if parsed is None or diameter_mm > family["max_diameter_mm"]:
        return None
    hole_zone, hole_grade, shaft_zone, shaft_grade = parsed
    hole_designation = f"{hole_zone}{hole_grade}"
    shaft_designation = f"{shaft_zone}{shaft_grade}"
    if diameter_mm > 500 and (hole_designation not in LARGE_HOLE_ZONES or shaft_designation not in LARGE_SHAFT_ZONES):
        return None
    tolerance_data = load_json("standard-tolerances.json")
    process_data = load_json("process-capability.json")
    hole_um = tolerance_width(diameter_mm, f"IT{hole_grade}", tolerance_data)
    shaft_um = tolerance_width(diameter_mm, f"IT{shaft_grade}", tolerance_data)
    if hole_um is None or shaft_um is None:
        return None
    row = tolerance_row(diameter_mm, tolerance_data)
    assert row is not None
    return {
        "status": "matched",
        "diameter_mm": diameter_mm,
        "diameter_step_mm": {"over": row["over_mm"], "through": row["through_mm"]},
        "family_id": family["id"],
        "family_name": family["name"],
        "fit_type": family["fit_type"],
        "recommended_fit": fit,
        "basis_system": "基孔制" if hole_zone == "H" else ("基轴制" if shaft_zone == "h" else "知识库列明的组合"),
        "assembly": family["assembly"],
        "selection_basis": family["basis"],
        "tolerance_widths": {
            "hole": {"zone": hole_designation, "grade": f"IT{hole_grade}", "um": hole_um, "mm": hole_um / 1000},
            "shaft": {"zone": shaft_designation, "grade": f"IT{shaft_grade}", "um": shaft_um, "mm": shaft_um / 1000},
        },
        "machining_candidates": {
            "hole": process_candidates("hole", hole_grade, process_data),
            "shaft": process_candidates("shaft", shaft_grade, process_data),
        },
        "compliance_note": "IT 数值只是公差宽度。上、下偏差和极限尺寸必须从对应公差带偏差表或已批准图样取值，不得将 IT 宽度自动对称分配。",
        "cost_note": process_data["cost_note"],
        "knowledge_sources": [
            "references/preferred-fits.md",
            "references/machining-and-cost.md",
            "references/data/standard-tolerances.json",
        ],
    }


def print_human(result: dict[str, Any]) -> None:
    widths = result["tolerance_widths"]
    print(f"推荐标注：⌀{result['diameter_mm']:g} {result['recommended_fit']}（{result['basis_system']}）")
    print(f"配合类型：{result['fit_type']} / {result['family_name']}")
    print(f"装配：{result['assembly']}")
    print(
        "公差宽度："
        f"孔 {widths['hole']['zone']} = {widths['hole']['um']:g} μm ({widths['hole']['mm']:g} mm)；"
        f"轴 {widths['shaft']['zone']} = {widths['shaft']['um']:g} μm ({widths['shaft']['mm']:g} mm)"
    )
    print(f"选择依据：{result['selection_basis']}")
    for surface, label in (("hole", "孔"), ("shaft", "轴")):
        values = result["machining_candidates"][surface]
        if not values:
            print(f"{label}加工：知识库未列出可用工艺。")
            continue
        rendered = []
        for item in values:
            cost = "成本档未列出" if item["relative_cost"] is None else f"相对成本 {item['relative_cost']}"
            rendered.append(f"{item['method']}（{item['capability']}，{cost}）")
        print(f"{label}终加工候选：" + "；".join(rendered))
    print("符合性：" + result["compliance_note"])
    print("成本说明：" + result["cost_note"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="仅使用附带知识库推荐孔轴配合。")
    parser.add_argument("--diameter-mm", type=float, help="基本尺寸，单位 mm。")
    parser.add_argument("--scene", help="配合场景描述。")
    parser.add_argument("--fit", help="直接查询知识库已列出的配合，例如 H7/g6。")
    parser.add_argument("--list-scenes", action="store_true", help="列出可匹配的知识库场景。")
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fit_data = load_json("preferred-fits.json")
    families = fit_data["families"]
    if args.list_scenes:
        for family in families:
            print(f"{family['id']}: {family['name']} -> {family['primary_fit']}")
        return 0
    if args.diameter_mm is None or (not args.scene and not args.fit):
        print(FALLBACK)
        return 2
    if args.fit:
        family = family_for_fit(args.fit, families)
        fit = args.fit
    else:
        family = family_for_scene(args.scene, families)
        fit = family["primary_fit"] if family else ""
    if family is None:
        print(FALLBACK)
        return 2
    result = make_result(args.diameter_mm, family, fit)
    if result is None:
        print(FALLBACK)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
