#!/usr/bin/env python3
"""Deterministic lookup helper for Coffee surface-roughness selection.

The calling agent must map the real engineering use case to one scenario. This
script deliberately does not pretend to understand arbitrary natural language.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCENARIOS = {
    "very-rough-non-mating": "very_rough_non_mating",
    "rough-before-weld": "rough_before_weld_or_rough_bore",
    "general-non-mating": "general_non_mating",
    "low-importance-fit": "low_importance_fit",
    "centering-or-key-working": "centering_or_key_working",
    "normal-precision-fit": "normal_precision_fit",
    "accurate-fit-or-bearing": "accurate_fit_or_bearing",
    "stable-fit-or-seal": "stable_fit_or_seal",
    "fatigue-or-airtight": "fatigue_or_airtight",
    "hydraulic-or-precision-centering": "hydraulic_or_precision_centering",
    "high-airtight-or-high-speed-friction": "high_airtight_or_high_speed_friction",
    "precision-instrument-or-gauge": "precision_instrument_or_gauge",
    "precision-measurement-or-large-gauge-block": "precision_measurement_or_large_gauge_block",
    "gauge-block-or-high-precision-support": "gauge_block_or_high_precision_support",
}


def load_catalog() -> dict:
    path = Path(__file__).resolve().parent.parent / "references" / "roughness-catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))


def recommendation(scenario: str) -> dict:
    catalog = load_catalog()
    functional_class = SCENARIOS[scenario]
    level = next(
        item for item in catalog["levels"] if item["functional_class"] == functional_class
    )
    return {
        "scenario": scenario,
        "parameter": catalog["parameter"],
        "unit": catalog["unit"],
        "recommended_ra_um": level["ra_um"],
        "surface": level["surface"],
        "typical_processes": level["processes"],
        "normative": catalog["normative"],
        "warning": "经验查表结果；最终值须结合图纸、配合、供应商规范和工艺能力确认。",
    }


def self_test() -> None:
    expected = {
        "general-non-mating": 12.5,
        "centering-or-key-working": 3.2,
        "normal-precision-fit": 1.6,
        "accurate-fit-or-bearing": 0.8,
        "stable-fit-or-seal": 0.4,
        "hydraulic-or-precision-centering": 0.1,
        "high-airtight-or-high-speed-friction": 0.05,
        "gauge-block-or-high-precision-support": 0.0063,
    }
    for scenario, ra in expected.items():
        actual = recommendation(scenario)["recommended_ra_um"]
        if actual != ra:
            raise AssertionError(f"{scenario}: expected {ra}, got {actual}")
    print(f"PASS: {len(expected)} representative scenarios")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--list-scenarios", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.list_scenarios:
        print("\n".join(sorted(SCENARIOS)))
        return
    if args.self_test:
        self_test()
        return
    if not args.scenario:
        parser.error("use --scenario, --list-scenarios, or --self-test")
    print(json.dumps(recommendation(args.scenario), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
