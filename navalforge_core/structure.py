"""Preliminary structural scantling estimates."""

from __future__ import annotations

from math import ceil, sqrt

from .constants import GRAVITY_M_S2
from .models import HydrostaticsResult, Project, WeightSummary


MATERIALS = {
    "aluminum": {
        "allowable_mpa": 95.0,
        "density_kg_m3": 2660.0,
        "commercial_mm": [3, 4, 5, 6, 8, 10, 12, 15, 20],
        "minimum_mm": 3.0,
    },
    "hdpe": {
        "allowable_mpa": 7.0,
        "density_kg_m3": 955.0,
        "commercial_mm": [8, 10, 12, 15, 20, 25, 30, 35, 40],
        "minimum_mm": 10.0,
    },
    "composite": {
        "allowable_mpa": 55.0,
        "density_kg_m3": 1650.0,
        "commercial_mm": [4, 5, 6, 8, 10, 12, 15, 18, 20, 25],
        "minimum_mm": 5.0,
    },
}


def _adopted(value_mm: float, gauges: list[int]) -> float:
    for gauge in gauges:
        if gauge >= value_mm:
            return float(gauge)
    return float(ceil(value_mm))


def preliminary_structure(
    project: Project,
    weights: WeightSummary,
    hydro: HydrostaticsResult,
) -> dict[str, object]:
    material = MATERIALS[project.material]
    speed_m_s = project.mission.max_speed_kn * 0.514444
    dynamic_kpa = 0.5 * project.water_density_kg_m3 * speed_m_s**2 / 1000.0
    hydro_kpa = project.water_density_kg_m3 * GRAVITY_M_S2 * hydro.draft_m / 1000.0
    bottom_pressure = max(15.0, hydro_kpa + 0.22 * dynamic_kpa)
    panels = [
        ("bottom", bottom_pressure, 0.42, 1.00),
        ("side", max(10.0, 0.55 * bottom_pressure), 0.48, 0.85),
        ("deck", max(6.0, 0.28 * bottom_pressure), 0.50, 0.70),
        ("bulkhead", max(5.0, hydro_kpa), 0.55, 0.72),
        ("transom", max(15.0, 0.85 * bottom_pressure), 0.38, 1.10),
        ("engine_reinforcement", max(20.0, bottom_pressure), 0.30, 1.30),
    ]
    results: list[dict[str, float | str]] = []
    for name, pressure_kpa, span_m, coefficient in panels:
        # Simplified plate bending screen: t = s*sqrt(k*p/sigma).
        calculated_m = span_m * sqrt(
            coefficient * pressure_kpa * 1000.0 / (float(material["allowable_mpa"]) * 1e6)
        )
        calculated_mm = max(float(material["minimum_mm"]), calculated_m * 1000.0)
        adopted = _adopted(calculated_mm, list(material["commercial_mm"]))
        results.append(
            {
                "element": name,
                "rule_or_method": "preliminary simply-supported plate pressure screen",
                "pressure_kpa": pressure_kpa,
                "allowable_stress_mpa": float(material["allowable_mpa"]),
                "safety_factor": 1.5,
                "span_m": span_m,
                "calculated_thickness_mm": calculated_mm,
                "adopted_commercial_thickness_mm": adopted,
                "governing_condition": "maximum-speed bottom pressure" if name in {"bottom", "transom", "engine_reinforcement"} else "local design pressure",
            }
        )
    return {
        "material": project.material,
        "elements": results,
        "frame_spacing_m": 0.45 if project.geometry.loa_m < 10.0 else 0.55,
        "longitudinal_spacing_m": 0.32 if project.geometry.loa_m < 10.0 else 0.38,
        "method": "preliminary pressure and plate-bending screening",
        "limitations": [
            "Does not replace detailed structural analysis, laminate schedule, weld design or class approval.",
            "Loads, boundary conditions and material allowables must be confirmed by the responsible engineer.",
        ],
    }
