"""Fuel, endurance, range and centre-shift calculations."""

from __future__ import annotations

from typing import Any

from .models import Project, WeightSummary


def fuel_analysis(
    project: Project,
    weights: WeightSummary,
    propulsion: dict[str, Any],
) -> dict[str, Any]:
    fuel_tanks = [tank for tank in project.tanks if tank.fluid in {"diesel", "gasoline"}]
    total_l = sum(tank.capacity_m3 * 1000.0 for tank in fuel_tanks)
    unusable_l = sum(
        tank.capacity_m3 * 1000.0 * tank.unusable_fraction for tank in fuel_tanks
    )
    expansion_l = 0.03 * total_l
    usable_before_reserve_l = max(0.0, total_l - unusable_l - expansion_l)
    reserve_l = 0.10 * usable_before_reserve_l
    usable_l = max(0.0, usable_before_reserve_l - reserve_l)

    selected = propulsion.get("selected_engine")
    max_l_h = float(selected["consumption_l_h_at_wot"]) if selected else (
        float(propulsion["maximum"]["power"]["required_installed_power_kw"]) * 0.32
    )
    cruise_required = float(propulsion["cruise"]["power"]["required_installed_power_kw"])
    max_required = max(float(propulsion["maximum"]["power"]["required_installed_power_kw"]), 1.0)
    cruise_load = min(0.95, max(0.25, cruise_required / max_required))
    cruise_l_h = max_l_h * (0.15 + 0.85 * cruise_load)
    endurance_h = usable_l / max(cruise_l_h, 0.1)
    range_nm = endurance_h * project.mission.cruise_speed_kn
    action_radius_nm = 0.45 * range_nm

    density = fuel_tanks[0].density_kg_m3 if fuel_tanks else 840.0
    departure_mass = total_l / 1000.0 * density
    arrival_mass = (unusable_l + reserve_l) / 1000.0 * density
    if fuel_tanks and departure_mass > 0.0:
        fuel_lcg = sum(tank.capacity_m3 * tank.lcg_m for tank in fuel_tanks) / sum(
            tank.capacity_m3 for tank in fuel_tanks
        )
        nonfuel_mass = max(0.0, weights.total_kg - departure_mass)
        nonfuel_lcg = (
            weights.total_kg * weights.lcg_m - departure_mass * fuel_lcg
        ) / max(nonfuel_mass, 1.0)
        arrival_lcg = (
            nonfuel_mass * nonfuel_lcg + arrival_mass * fuel_lcg
        ) / max(nonfuel_mass + arrival_mass, 1.0)
    else:
        fuel_lcg = weights.lcg_m
        arrival_lcg = weights.lcg_m
    return {
        "fuel_total_l": total_l,
        "fuel_usable_l": usable_l,
        "fuel_unusable_l": unusable_l,
        "reserve_l": reserve_l,
        "expansion_l": expansion_l,
        "density_kg_m3": density,
        "departure_fuel_mass_kg": departure_mass,
        "arrival_fuel_mass_kg": arrival_mass,
        "maximum_consumption_l_h": max_l_h,
        "cruise_consumption_l_h": cruise_l_h,
        "endurance_h": endurance_h,
        "range_nm": range_nm,
        "action_radius_nm": action_radius_nm,
        "fuel_lcg_m": fuel_lcg,
        "departure_lcg_m": weights.lcg_m,
        "arrival_lcg_m": arrival_lcg,
        "method": "usable fuel / demonstrative engine consumption at estimated cruise load",
        "warnings": [
            "Consumption must be replaced by verified engine/propulsor curves for contractual use."
        ],
    }
