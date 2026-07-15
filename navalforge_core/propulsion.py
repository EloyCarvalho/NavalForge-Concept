"""Required power and demonstrative motor matching."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .resistance import calculate_resistance_point
from .models import HydrostaticsResult, Project, WeightSummary


def required_power(
    project: Project,
    resistance: dict[str, Any],
) -> dict[str, float]:
    effective = float(resistance["effective_power_kw"])
    delivered = effective / (project.propulsive_efficiency * project.transmission_efficiency)
    factor = (
        (1.0 + project.sea_margin_fraction)
        * (1.0 + project.growth_margin_fraction)
        * (1.0 + project.power_reserve_fraction)
    )
    return {
        "effective_power_kw": effective,
        "delivered_power_kw": delivered,
        "required_installed_power_kw": delivered * factor,
        "overall_efficiency": project.propulsive_efficiency * project.transmission_efficiency,
        "combined_margin_factor": factor,
    }


def load_engine_database(path: Path | None = None) -> list[dict[str, Any]]:
    if path is None:
        path = Path(__file__).resolve().parents[1] / "databases" / "engines" / "engines.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def match_engines(
    project: Project,
    required_kw: float,
    engines: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    engines = engines if engines is not None else load_engine_database()
    matches: list[dict[str, Any]] = []
    for engine in engines:
        if project.propulsion_type not in engine.get("installations", []):
            continue
        for quantity in (1, 2, 3, 4):
            total = quantity * float(engine["power_kw"])
            margin = total / max(required_kw, 1.0) - 1.0
            if 0.0 <= margin <= 0.80:
                matches.append(
                    {
                        "manufacturer": engine["manufacturer"],
                        "model": engine["model"],
                        "quantity": quantity,
                        "power_total_kw": total,
                        "power_total_hp": total / 0.745699872,
                        "weight_total_kg": quantity * float(engine["weight_kg"]),
                        "power_margin_fraction": margin,
                        "fuel": engine["fuel"],
                        "consumption_l_h_at_wot": quantity * float(engine["consumption_l_h_at_wot"]),
                        "compatibility": "compatible",
                        "advantages": engine.get("advantages", []),
                        "limitations": engine.get("limitations", []),
                        "demo_price_brl": quantity * float(engine.get("demo_price_brl", 0.0)),
                        "price_notice": "Synthetic demonstrative price; not a current quotation.",
                    }
                )
    return sorted(matches, key=lambda item: (item["power_margin_fraction"], item["weight_total_kg"]))[:8]


def propulsion_analysis(
    project: Project,
    weights: WeightSummary,
    hydro: HydrostaticsResult,
) -> dict[str, Any]:
    maximum_resistance = calculate_resistance_point(
        project, weights, hydro, project.mission.max_speed_kn
    )
    cruise_resistance = calculate_resistance_point(
        project, weights, hydro, project.mission.cruise_speed_kn
    )
    maximum_power = required_power(project, maximum_resistance)
    cruise_power = required_power(project, cruise_resistance)
    matches = match_engines(project, maximum_power["required_installed_power_kw"])
    return {
        "maximum": {"resistance": maximum_resistance, "power": maximum_power},
        "cruise": {"resistance": cruise_resistance, "power": cruise_power},
        "compatible_engines": matches,
        "selected_engine": matches[0] if matches else None,
        "warnings": [] if matches else ["No demonstrative engine combination matched the required power and installation type."],
    }
