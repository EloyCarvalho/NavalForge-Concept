"""Preliminary planing resistance and performance estimates."""

from __future__ import annotations

from math import log10, radians, sqrt, tan

from .constants import GRAVITY_M_S2, KNOT_TO_M_S
from .models import HydrostaticsResult, Project, WeightSummary


def calculate_resistance_point(
    project: Project,
    weights: WeightSummary,
    hydro: HydrostaticsResult,
    speed_kn: float,
) -> dict[str, float | str | list[str]]:
    speed_m_s = speed_kn * KNOT_TO_M_S
    fn = speed_m_s / sqrt(GRAVITY_M_S2 * project.geometry.lwl_m)
    beta = project.geometry.deadrise_deg
    trim_dynamic = max(2.0, min(7.5, 5.6 - 1.6 * fn + 0.025 * beta))
    wetted_length = project.geometry.lwl_m * max(0.30, min(0.92, 0.90 - 0.42 * fn))
    wetted_beam = project.geometry.chine_beam_m * max(0.72, 1.0 - 0.10 * fn)
    wetted_area = max(
        0.5,
        wetted_length * wetted_beam / max(0.45, 0.85 * (1.0 - beta / 120.0)),
    )
    reynolds = max(1e5, speed_m_s * wetted_length / 1.19e-6)
    cf = 0.075 / (log10(reynolds) - 2.0) ** 2
    friction_n = 0.5 * project.water_density_kg_m3 * speed_m_s**2 * wetted_area * cf
    pressure_n = weights.total_kg * GRAVITY_M_S2 * tan(radians(trim_dynamic)) * 0.34
    appendage_n = 0.06 * (friction_n + pressure_n)
    air_n = 0.5 * 1.225 * speed_m_s**2 * project.air_drag_area_m2 * 0.9
    total_n = friction_n + pressure_n + appendage_n + air_n
    effective_kw = total_n * speed_m_s / 1000.0
    lcg_ratio = weights.lcg_m / project.geometry.lwl_m
    porpoising_risk = max(
        0.0,
        min(1.0, 0.22 + 0.65 * max(0.0, lcg_ratio - 0.42) + 0.04 * max(0.0, trim_dynamic - 5.0)),
    )
    warnings: list[str] = []
    if fn < 0.60:
        warnings.append("Speed is below the preferred planing-method range; displacement effects are simplified.")
    if fn > 3.0:
        warnings.append("Froude number is outside the configured preliminary planing range.")
    if beta < 8.0 or beta > 30.0:
        warnings.append("Deadrise is outside the configured Savitsky screening range (8-30 deg).")
    return {
        "speed_kn": speed_kn,
        "speed_m_s": speed_m_s,
        "froude_number": fn,
        "dynamic_trim_deg": trim_dynamic,
        "wetted_length_m": wetted_length,
        "wetted_area_m2": wetted_area,
        "friction_resistance_n": friction_n,
        "pressure_resistance_n": pressure_n,
        "appendage_resistance_n": appendage_n,
        "air_resistance_n": air_n,
        "total_resistance_n": total_n,
        "effective_power_kw": effective_kw,
        "porpoising_risk": porpoising_risk,
        "method": "Savitsky-inspired prismatic planing screening + ITTC-1957 friction line",
        "warnings": warnings,
    }


def resistance_curve(
    project: Project,
    weights: WeightSummary,
    hydro: HydrostaticsResult,
) -> list[dict[str, float | str | list[str]]]:
    low = max(5.0, 0.45 * project.mission.cruise_speed_kn)
    high = project.mission.max_speed_kn * 1.05
    count = 9
    return [
        calculate_resistance_point(
            project,
            weights,
            hydro,
            low + index * (high - low) / (count - 1),
        )
        for index in range(count)
    ]
