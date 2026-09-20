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

CONNECTION_FAMILIES = {
    "moving": {
        "precision_sliding",
        "normal_running",
        "large_clearance_running",
        "loose_running",
        "very_loose_running",
        "high_temperature_running",
    },
    "locating": {
        "precision_location_clearance",
        "loose_location_clearance",
        "loose_transition",
        "light_transition",
        "medium_transition",
        "tight_transition",
    },
    "press": {
        "standard_press",
        "light_press",
        "medium_press",
        "heavy_press",
        "extra_heavy_press",
    },
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


def families_for_scene(
    scene: str,
    families: list[dict[str, Any]],
    allowed_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    normalized = "".join(scene.lower().split())
    ranked: list[tuple[int, int, int, dict[str, Any]]] = []
    for family in families:
        if allowed_ids is not None and family["id"] not in allowed_ids:
            continue
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
    ranked.sort(key=lambda item: item[:3], reverse=True)
    return [item[3] for item in ranked]


def family_for_scene(
    scene: str,
    families: list[dict[str, Any]],
    allowed_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    matched = families_for_scene(scene, families, allowed_ids)
    if len(matched) != 1:
        return None
    return matched[0]


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
    hole_processes = process_candidates("hole", hole_grade, process_data)
    shaft_processes = process_candidates("shaft", shaft_grade, process_data)
    if not hole_processes or not shaft_processes:
        return None
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
            "hole": hole_processes,
            "shaft": shaft_processes,
        },
        "compliance_note": "IT 数值只是公差宽度。上、下偏差和极限尺寸必须从对应公差带偏差表或已批准图样取值，不得将 IT 宽度自动对称分配。",
        "cost_note": process_data["cost_note"],
        "knowledge_sources": [
            "references/preferred-fits.md",
            "references/machining-and-cost.md",
            "references/data/standard-tolerances.json",
        ],
    }


def information_questions(args: argparse.Namespace) -> list[dict[str, str]]:
    """Return only questions whose answers can change the recommendation."""
    questions: list[dict[str, str]] = []

    def add(field: str, question: str, impact: str) -> None:
        if getattr(args, field, None) in (None, ""):
            questions.append({"field": field, "question": question, "impact": impact})

    add("diameter_mm", "孔轴配合的基本直径是多少 mm？", "尺寸段决定 IT 公差宽度及可用公差带。")
    add("scene", "这个配合部位具体用来做什么，孔和轴分别是哪两个零件？", "用途决定应匹配哪个知识库应用场景。")
    add("connection", "它属于相对运动、定位对中，还是靠过盈固定/传递载荷？", "这会先决定间隙、过渡或过盈配合分支。")
    add("motion", "孔轴之间是固定、连续/间歇旋转、轴向滑动，还是往复运动？", "运动形式会改变所需间隙和配合家族。")
    add("precision", "定心、同轴或导向精度要求是低、中还是高？", "精度目标会影响公差等级及松紧程度。")

    if args.connection == "moving":
        add("speed", "转速、线速度或往复频率是多少（也可说明低/中/高）？", "速度会影响油膜和工作间隙需求。")
        add("load", "载荷是轻、中还是重，是否存在冲击、振动或侧向载荷？", "载荷会影响间隙大小及精度档。")
        add("lubrication", "采用无润滑、油润滑、脂润滑还是其他方式？", "润滑条件决定是否必须保留稳定油膜间隙。")
        add("temperature", "工作温度是否稳定，是否明显发热、高温或孔轴温差较大？", "热变形可能要求增大间隙或改用专门场景。")
        add("sealing", "若为活塞、阀芯或柱塞，密封由密封圈/油膜承担，还是由该配合圆柱面承担？", "密封与导向的分工会改变允许间隙。")
    elif args.connection == "locating":
        add("disassembly", "该连接需要频繁、偶尔拆卸，还是基本不拆？", "拆装频率用于区分 h、js、k、m、n 等家族。")
        add("assembly", "允许手推/手旋、锤击、压力机，还是温差装配？", "装配方式限制可选的过渡紧度。")
        add("vibration", "工作中是否有明显振动或冲击？", "是否需要用少量过盈消除振动取决于此项。")
        add("torque_path", "转矩由键/销/紧固件传递，还是依赖配合面摩擦？", "转矩路径决定定位配合能否保持间隙。")
    elif args.connection == "press":
        add("materials", "孔件和轴件分别是什么材料？", "铁类与非铁类材料对应的压入性质和许用应力不同。")
        add("load", "需传递的载荷或转矩是较小、较大还是很大，是否有变载冲击？", "载荷决定轻型、中型、重型或特重型压入。")
        add("vibration", "工作中是否有明显振动或冲击？", "冲击振动可能提高所需过盈档。")
        add("auxiliary_fastener", "是否有键、销、螺栓等辅助紧固件传递转矩？", "有无辅助紧固件会改变过盈量需求。")
        add("disassembly", "该连接需要时易拆、半永久，还是永久装配？", "拆卸要求用于排除过重的过盈配合。")
        add("assembly", "可使用锤击、压力机或热胀冷缩中的哪些装配方式？", "装配能力限制可实现的过盈等级。")
        add("material_strength", "材料强度是否已校核并允许采用目标过盈档？", "重型过盈必须受材料许用应力约束。")

    return questions[:5]


def print_questions(questions: list[dict[str, str]], as_json: bool) -> None:
    payload = {"status": "need_more_information", "questions": questions}
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print("现有信息不足，暂不推荐公差配合。还需要确认：")
    for index, item in enumerate(questions, start=1):
        print(f"{index}. {item['question']} {item['impact']}")


def print_human(result: dict[str, Any]) -> None:
    widths = result["tolerance_widths"]
    print("信息充分性：已通过门禁；关键条件齐全并唯一命中一个知识库配合家族。")
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
    parser.add_argument("--connection", choices=sorted(CONNECTION_FAMILIES), help="推荐模式分支：moving、locating 或 press。")
    parser.add_argument("--motion", help="固定、连续/间歇旋转、轴向滑动或往复。")
    parser.add_argument("--precision", choices=["low", "medium", "high"], help="定心、同轴或导向精度。")
    parser.add_argument("--speed", help="转速、线速度、往复频率，或 low/medium/high。")
    parser.add_argument("--load", help="载荷/转矩及冲击情况。")
    parser.add_argument("--lubrication", help="无润滑、油、脂或其他润滑。")
    parser.add_argument("--temperature", help="温度稳定、发热、高温或温差情况。")
    parser.add_argument("--sealing", help="密封方式及密封/导向分工。")
    parser.add_argument("--disassembly", help="拆卸频率或永久性要求。")
    parser.add_argument("--assembly", help="手装、锤击、压力机或温差装配。")
    parser.add_argument("--vibration", help="振动和冲击情况。")
    parser.add_argument("--torque-path", dest="torque_path", help="键/紧固件或配合摩擦传递转矩。")
    parser.add_argument("--materials", help="孔件和轴件材料。")
    parser.add_argument("--auxiliary-fastener", dest="auxiliary_fastener", help="辅助键、销或紧固件。")
    parser.add_argument("--material-strength", dest="material_strength", help="材料许用应力/过盈强度校核情况。")
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

    if args.diameter_mm is not None and tolerance_row(args.diameter_mm, load_json("standard-tolerances.json")) is None:
        print(FALLBACK)
        return 2

    if args.fit:
        if args.diameter_mm is None:
            print_questions(information_questions(args)[:1], args.json)
            return 3
        family = family_for_fit(args.fit, families)
        fit = args.fit
    else:
        questions = information_questions(args)
        if questions:
            print_questions(questions, args.json)
            return 3
        allowed_ids = CONNECTION_FAMILIES[args.connection]
        matched = families_for_scene(args.scene, families, allowed_ids)
        if len(matched) > 1:
            names = "、".join(item["name"] for item in matched)
            print_questions(
                [
                    {
                        "field": "scene_disambiguation",
                        "question": f"当前描述同时命中“{names}”。请说明哪个应用特征是主要约束？",
                        "impact": "只有排除其余候选后，才能唯一确定配合家族。",
                    }
                ],
                args.json,
            )
            return 3
        family = matched[0] if matched else None
        fit = family["primary_fit"] if family else ""
    if family is None:
        print(FALLBACK)
        return 2
    result = make_result(args.diameter_mm, family, fit)
    if result is None:
        print(FALLBACK)
        return 2
    result["information_gate"] = "passed" if not args.fit else "direct_fit_lookup"
    if not args.fit:
        result["input_facts"] = {
            key: value
            for key, value in vars(args).items()
            if value not in (None, False, "") and key not in {"json", "list_scenes", "fit"}
        }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
