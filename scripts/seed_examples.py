"""Create three synthetic demonstration projects and report bundles."""

from __future__ import annotations

import json
from pathlib import Path

from navalforge_core.evaluator import evaluate_project
from navalforge_core.models import Project
from navalforge_core.reports import generate_report_bundle

ROOT = Path(__file__).resolve().parents[1]


def req(
    id_: str,
    description: str,
    metric: str,
    operator: str,
    value: float | str,
    unit: str,
    kind: str = "mandatory",
    priority: int = 5,
) -> dict:
    return {
        "id": id_,
        "description": description,
        "category": "mission",
        "metric": metric,
        "operator": operator,
        "value": value,
        "unit": unit,
        "source": "synthetic demonstration brief",
        "priority": priority,
        "acceptance_criterion": f"Calculated {metric} {operator} {value} {unit}",
        "verification_method": "NavalForge preliminary calculation",
        "notes": "Synthetic requirement for software demonstration.",
        "revision": "R1",
        "kind": kind,
    }


def weight(
    id_: str,
    description: str,
    group: str,
    mass: float,
    lcg: float,
    vcg: float,
    confidence: float = 0.75,
    margin: float = 0.0,
    status: str = "estimated",
) -> dict:
    return {
        "id": id_,
        "description": description,
        "group": group,
        "quantity": 1,
        "unit_weight_kg": mass,
        "lcg_m": lcg,
        "tcg_m": 0,
        "vcg_m": vcg,
        "source": "synthetic conceptual estimate",
        "confidence": confidence,
        "margin_fraction": margin,
        "revision": "W1",
        "status": status,
        "active": True,
    }


def service_7m() -> dict:
    return {
        "project_id": "NF-DEMO-SERVICE-7M",
        "name": "7 m service launch",
        "revision": "P1",
        "description": "Synthetic demonstrative aluminum service launch.",
        "material": "aluminum",
        "propulsion_type": "outboard",
        "mission": {
            "vessel_type": "service",
            "navigation_area": "coastal",
            "cruise_speed_kn": 24,
            "max_speed_kn": 34,
            "endurance_h": 4,
            "target_range_nm": 80,
            "crew": 2,
            "passengers": 4,
            "payload_kg": 300,
        },
        "geometry": {
            "revision": "G1",
            "loa_m": 7.0,
            "lwl_m": 6.4,
            "beam_m": 2.35,
            "chine_beam_m": 1.95,
            "depth_m": 1.18,
            "deadrise_deg": 16,
            "flare_deg": 13,
            "transom_beam_m": 1.76,
            "chine_count": 1,
            "design_draft_m": 0.46,
            "bow_rise_m": 0.32,
            "stations": 41,
        },
        "weights": [
            weight("W7-01", "Hull and primary structure", "hull_structure", 720, 3.15, 0.54, margin=0.08),
            weight("W7-02", "Deck outfit", "deck", 210, 3.25, 0.92),
            weight("W7-03", "Console and shelter", "superstructure", 120, 3.55, 1.22),
            weight("W7-04", "Outboard propulsion allowance", "propulsion", 230, 0.25, 0.78),
            weight("W7-05", "Electrical system", "electrical", 85, 2.60, 0.78),
            weight("W7-06", "Navigation package", "navigation", 35, 3.40, 1.35),
            weight("W7-07", "Safety equipment", "safety", 65, 4.00, 0.95),
            weight("W7-08", "Furniture and outfit", "furniture", 90, 3.55, 0.92),
            weight("W7-09", "Explicit weight reserve", "margins", 100, 3.20, 0.75, confidence=0.5, status="margin"),
        ],
        "tanks": [
            {
                "id": "T7-FUEL",
                "description": "Gasoline tank",
                "fluid": "gasoline",
                "shape": "rectangular",
                "length_m": 1.20,
                "width_m": 0.60,
                "height_m": 0.30,
                "fill_fraction": 0.95,
                "density_kg_m3": 745,
                "lcg_m": 2.85,
                "tcg_m": 0,
                "vcg_m": 0.56,
                "unusable_fraction": 0.03,
            }
        ],
        "loading_conditions": [
            {
                "id": "LC-DEPARTURE",
                "name": "Departure - full mission load",
                "tank_fills": {"T7-FUEL": 0.95},
                "people_count": 6,
                "person_mass_kg": 85,
                "people_lcg_m": 3.55,
                "people_vcg_m": 1.05,
                "cargo_mass_kg": 300,
                "cargo_lcg_m": 3.10,
                "cargo_vcg_m": 0.72,
                "revision": "LC1",
            }
        ],
        "active_condition_id": "LC-DEPARTURE",
        "requirements": [
            req("REQ7-LOA", "Overall length shall not exceed 7.50 m", "loa_m", "<=", 7.5, "m"),
            req("REQ7-SPEED", "Maximum speed shall be at least 30 kn", "max_speed_kn", ">=", 30, "kn"),
            req("REQ7-RANGE", "Range shall be at least 75 nmi", "range_nm", ">=", 75, "nmi"),
            req("REQ7-GM", "Preliminary corrected GM shall exceed 0.35 m", "gm_m", ">=", 0.35, "m"),
            req("REQ7-FB", "Preliminary freeboard shall exceed 0.40 m", "freeboard_m", ">=", 0.40, "m"),
            req("REQ7-PAYLOAD", "Payload shall be at least 300 kg", "payload_kg", ">=", 300, "kg"),
        ],
        "downflooding_points": [
            {"id": "DF7-01", "x_m": 3.8, "y_m": 1.02, "z_m": 1.05, "description": "Cockpit sill demonstration"}
        ],
        "propulsive_efficiency": 0.58,
        "transmission_efficiency": 0.98,
        "estimated_build_cost_brl": 270000,
        "air_drag_area_m2": 2.6,
        "assumptions": [
            "All project and price data are synthetic demonstrations.",
            "Departure condition includes six people and mission payload.",
        ],
    }


def patrol_10m() -> dict:
    return {
        "project_id": "NF-DEMO-PATROL-10M",
        "name": "10 m patrol launch",
        "revision": "P1",
        "description": "Synthetic demonstrative aluminum patrol launch with waterjets.",
        "material": "aluminum",
        "propulsion_type": "waterjet",
        "mission": {
            "vessel_type": "patrol",
            "navigation_area": "coastal/offshore transition",
            "cruise_speed_kn": 28,
            "max_speed_kn": 38,
            "endurance_h": 7,
            "target_range_nm": 180,
            "crew": 3,
            "passengers": 5,
            "payload_kg": 500,
        },
        "geometry": {
            "revision": "G1",
            "loa_m": 10.0,
            "lwl_m": 9.2,
            "beam_m": 3.10,
            "chine_beam_m": 2.55,
            "depth_m": 1.55,
            "deadrise_deg": 18,
            "flare_deg": 15,
            "transom_beam_m": 2.35,
            "chine_count": 1,
            "design_draft_m": 0.62,
            "bow_rise_m": 0.48,
            "stations": 51,
        },
        "weights": [
            weight("W10-01", "Hull and primary structure", "hull_structure", 2400, 4.55, 0.68, margin=0.08),
            weight("W10-02", "Deck outfit", "deck", 650, 4.70, 1.18),
            weight("W10-03", "Wheelhouse and superstructure", "superstructure", 700, 5.10, 1.55),
            weight("W10-04", "Twin engine and jet allowance", "propulsion", 820, 2.05, 0.72),
            weight("W10-05", "Electrical and hydraulic systems", "electrical", 220, 4.25, 0.92),
            weight("W10-06", "Navigation and communications", "navigation", 100, 5.25, 1.80),
            weight("W10-07", "Safety and mission equipment", "safety", 140, 5.65, 1.12),
            weight("W10-08", "Furniture and outfit", "furniture", 280, 5.05, 1.20),
            weight("W10-09", "Explicit weight reserve", "margins", 300, 4.55, 0.95, confidence=0.5, status="margin"),
        ],
        "tanks": [
            {
                "id": "T10-FUEL",
                "description": "Main diesel tank",
                "fluid": "diesel",
                "shape": "rectangular",
                "length_m": 1.80,
                "width_m": 1.00,
                "height_m": 0.65,
                "fill_fraction": 0.95,
                "density_kg_m3": 840,
                "lcg_m": 4.15,
                "tcg_m": 0,
                "vcg_m": 0.74,
                "unusable_fraction": 0.03,
            }
        ],
        "loading_conditions": [
            {
                "id": "LC-DEPARTURE",
                "name": "Patrol departure",
                "tank_fills": {"T10-FUEL": 0.95},
                "people_count": 8,
                "person_mass_kg": 85,
                "people_lcg_m": 5.15,
                "people_vcg_m": 1.30,
                "cargo_mass_kg": 500,
                "cargo_lcg_m": 4.85,
                "cargo_vcg_m": 0.85,
                "revision": "LC1",
            }
        ],
        "requirements": [
            req("REQ10-LOA", "Overall length shall not exceed 10.50 m", "loa_m", "<=", 10.5, "m"),
            req("REQ10-BEAM", "Beam shall not exceed 3.30 m", "beam_m", "<=", 3.3, "m"),
            req("REQ10-SPEED", "Maximum speed shall be at least 35 kn", "max_speed_kn", ">=", 35, "kn"),
            req("REQ10-RANGE", "Range shall be at least 170 nmi", "range_nm", ">=", 170, "nmi"),
            req("REQ10-GM", "Preliminary corrected GM shall exceed 0.45 m", "gm_m", ">=", 0.45, "m"),
            req("REQ10-FB", "Preliminary freeboard shall exceed 0.50 m", "freeboard_m", ">=", 0.50, "m"),
            req("REQ10-PAYLOAD", "Payload shall be at least 500 kg", "payload_kg", ">=", 500, "kg"),
        ],
        "downflooding_points": [
            {"id": "DF10-01", "x_m": 5.8, "y_m": 1.42, "z_m": 1.38, "description": "Wheelhouse door sill demonstration"}
        ],
        "propulsive_efficiency": 0.60,
        "transmission_efficiency": 0.96,
        "estimated_build_cost_brl": 1450000,
        "air_drag_area_m2": 5.8,
        "assumptions": [
            "All project and price data are synthetic demonstrations.",
            "Waterjet package is represented by aggregate demonstrative data.",
        ],
    }


def rescue_12m() -> dict:
    return {
        "project_id": "NF-DEMO-RESCUE-12M",
        "name": "12 m rescue and support craft",
        "revision": "P1",
        "description": "Synthetic demonstrative composite rescue/support craft.",
        "material": "composite",
        "propulsion_type": "shaft",
        "mission": {
            "vessel_type": "rescue/support",
            "navigation_area": "offshore coastal",
            "cruise_speed_kn": 24,
            "max_speed_kn": 35,
            "endurance_h": 10,
            "target_range_nm": 240,
            "crew": 4,
            "passengers": 8,
            "payload_kg": 1000,
        },
        "geometry": {
            "revision": "G1",
            "loa_m": 12.0,
            "lwl_m": 11.1,
            "beam_m": 3.55,
            "chine_beam_m": 2.95,
            "depth_m": 1.85,
            "deadrise_deg": 20,
            "flare_deg": 17,
            "transom_beam_m": 2.70,
            "chine_count": 2,
            "design_draft_m": 0.78,
            "bow_rise_m": 0.62,
            "stations": 61,
        },
        "weights": [
            weight("W12-01", "Composite hull and primary structure", "hull_structure", 4500, 5.45, 0.82, margin=0.08),
            weight("W12-02", "Deck outfit", "deck", 1200, 5.60, 1.36),
            weight("W12-03", "Wheelhouse and superstructure", "superstructure", 1000, 6.15, 1.78),
            weight("W12-04", "Twin inboard propulsion allowance", "propulsion", 1800, 3.20, 0.82),
            weight("W12-05", "Electrical and hydraulic systems", "electrical", 400, 5.10, 1.05),
            weight("W12-06", "Navigation and communications", "navigation", 150, 6.15, 2.05),
            weight("W12-07", "Rescue and safety equipment", "safety", 300, 7.10, 1.18),
            weight("W12-08", "Furniture and accommodation", "furniture", 500, 6.10, 1.32),
            weight("W12-09", "Explicit weight reserve", "margins", 500, 5.50, 1.05, confidence=0.5, status="margin"),
        ],
        "tanks": [
            {
                "id": "T12-FUEL-P",
                "description": "Port diesel tank",
                "fluid": "diesel",
                "shape": "rectangular",
                "length_m": 1.70,
                "width_m": 1.00,
                "height_m": 0.70,
                "fill_fraction": 0.92,
                "density_kg_m3": 840,
                "lcg_m": 4.65,
                "tcg_m": -0.72,
                "vcg_m": 0.84,
                "unusable_fraction": 0.03,
            },
            {
                "id": "T12-FUEL-S",
                "description": "Starboard diesel tank",
                "fluid": "diesel",
                "shape": "rectangular",
                "length_m": 1.70,
                "width_m": 1.00,
                "height_m": 0.70,
                "fill_fraction": 0.92,
                "density_kg_m3": 840,
                "lcg_m": 4.65,
                "tcg_m": 0.72,
                "vcg_m": 0.84,
                "unusable_fraction": 0.03,
            },
        ],
        "loading_conditions": [
            {
                "id": "LC-DEPARTURE",
                "name": "Rescue departure",
                "tank_fills": {"T12-FUEL-P": 0.92, "T12-FUEL-S": 0.92},
                "people_count": 12,
                "person_mass_kg": 85,
                "people_lcg_m": 6.25,
                "people_vcg_m": 1.45,
                "cargo_mass_kg": 1000,
                "cargo_lcg_m": 6.40,
                "cargo_vcg_m": 0.95,
                "revision": "LC1",
            }
        ],
        "requirements": [
            req("REQ12-LOA", "Overall length shall not exceed 12.50 m", "loa_m", "<=", 12.5, "m"),
            req("REQ12-SPEED", "Maximum speed shall be at least 32 kn", "max_speed_kn", ">=", 32, "kn"),
            req("REQ12-RANGE", "Range shall be at least 220 nmi", "range_nm", ">=", 220, "nmi"),
            req("REQ12-GM", "Preliminary corrected GM shall exceed 0.50 m", "gm_m", ">=", 0.50, "m"),
            req("REQ12-FB", "Preliminary freeboard shall exceed 0.60 m", "freeboard_m", ">=", 0.60, "m"),
            req("REQ12-PAYLOAD", "Payload shall be at least 1000 kg", "payload_kg", ">=", 1000, "kg"),
        ],
        "downflooding_points": [
            {"id": "DF12-01", "x_m": 6.8, "y_m": 1.60, "z_m": 1.62, "description": "Rescue deck access sill demonstration"}
        ],
        "propulsive_efficiency": 0.62,
        "transmission_efficiency": 0.97,
        "estimated_build_cost_brl": 2800000,
        "air_drag_area_m2": 8.5,
        "assumptions": [
            "All project and price data are synthetic demonstrations.",
            "Composite laminate properties are placeholders for conceptual screening.",
        ],
    }


def main() -> None:
    examples = ROOT / "examples"
    generated = examples / "generated"
    examples.mkdir(exist_ok=True)
    generated.mkdir(exist_ok=True)
    for raw in (service_7m(), patrol_10m(), rescue_12m()):
        project = Project.model_validate(raw)
        project_path = examples / f"{project.project_id.lower()}.json"
        project_path.write_text(
            json.dumps(project.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        result = evaluate_project(project, include_variants=True)
        generate_report_bundle(project, result, generated)
        print(
            project.project_id,
            result.status,
            f"mass={result.indicators['displacement_kg']:.1f} kg",
            f"GM={result.indicators['gm_m']:.3f} m",
            f"range={result.indicators['range_nm']:.1f} nmi",
        )


if __name__ == "__main__":
    main()
