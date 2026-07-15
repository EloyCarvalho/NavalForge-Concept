"""Integrated NavalForge evaluation pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .constants import ALGORITHM_VERSION
from .equilibrium import solve_equilibrium
from .fuel import fuel_analysis
from .geometry import mesh_payload
from .models import AuditResult, EvaluationResult, Project
from .propulsion import propulsion_analysis
from .requirements import verify_requirements
from .resistance import resistance_curve
from .stability import calculate_stability
from .structure import preliminary_structure
from .weights import calculate_weights, individual_weight_totals


def _audit(
    value: Any,
    unit: str,
    method: str,
    project: Project,
    equation: str = "",
    reference: str = "",
    inputs: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    compliance: str = "informative",
) -> dict[str, Any]:
    return AuditResult(
        value=value,
        unit=unit,
        method=method,
        equation=equation,
        reference=reference,
        loading_condition=project.active_condition_id,
        geometry_revision=project.geometry.revision,
        weight_revision=max((item.revision for item in project.weights), default="W0"),
        algorithm_version=ALGORITHM_VERSION,
        inputs=inputs or {},
        assumptions=project.assumptions,
        warnings=warnings or [],
        compliance=compliance,
    ).model_dump(mode="json")


def evaluate_single(project: Project) -> EvaluationResult:
    """Run one design through the exact same auditable engineering pipeline."""
    weights = calculate_weights(project)
    hydro = solve_equilibrium(
        project.geometry,
        weights.total_kg,
        weights.lcg_m,
        project.water_density_kg_m3,
        project.geometry.design_draft_m,
    )
    stability = calculate_stability(project, weights, hydro)
    propulsion = propulsion_analysis(project, weights, hydro)
    fuel = fuel_analysis(project, weights, propulsion)
    structure = preliminary_structure(project, weights, hydro)
    curve = resistance_curve(project, weights, hydro)

    selected_engine = propulsion.get("selected_engine")
    required_kw = float(propulsion["maximum"]["power"]["required_installed_power_kw"])
    installed_kw = float(selected_engine["power_total_kw"]) if selected_engine else required_kw
    achieved_speed = project.mission.max_speed_kn if selected_engine else 0.85 * project.mission.max_speed_kn
    metrics = {
        "loa_m": project.geometry.loa_m,
        "lwl_m": project.geometry.lwl_m,
        "beam_m": project.geometry.beam_m,
        "draft_m": hydro.draft_m,
        "freeboard_m": hydro.freeboard_m,
        "displacement_kg": weights.total_kg,
        "max_speed_kn": achieved_speed,
        "cruise_speed_kn": project.mission.cruise_speed_kn,
        "range_nm": fuel["range_nm"],
        "endurance_h": fuel["endurance_h"],
        "gm_m": stability["gm_corrected_m"],
        "payload_kg": project.mission.payload_kg,
        "installed_power_kw": installed_kw,
        "required_power_kw": required_kw,
        "material": project.material,
        "propulsion_type": project.propulsion_type,
        "cost_brl": project.estimated_build_cost_brl + float(selected_engine.get("demo_price_brl", 0.0) if selected_engine else 0.0),
    }
    requirements = verify_requirements(project, metrics)
    warnings: list[str] = []
    warnings.extend(stability["warnings"])
    warnings.extend(propulsion["warnings"])
    warnings.extend(fuel["warnings"])
    if not hydro.converged:
        warnings.append("Equilibrium solver did not meet configured residual tolerances.")
    for point in curve:
        warnings.extend(str(item) for item in point.get("warnings", []))
    warnings = list(dict.fromkeys(warnings))

    status = requirements["status"]
    if requirements["mandatory_gate_passed"] and warnings:
        status = "CONDITIONAL — preliminary results with active engineering reservations"
    traceability = {
        "displacement": _audit(
            weights.total_kg,
            "kg",
            "sum of active mass points",
            project,
            "W = Σ(q × unit_weight × (1 + margin))",
            inputs={"item_count": len(project.weights)},
        ),
        "draft": _audit(
            hydro.draft_m,
            "m",
            hydro.method,
            project,
            "buoyancy(draft, trim) = weight; LCB(draft, trim) = LCG",
            inputs={"mass_kg": weights.total_kg, "lcg_m": weights.lcg_m},
            warnings=[] if hydro.converged else ["Solver residual tolerance not met"],
        ),
        "gm": _audit(
            stability["gm_corrected_m"],
            "m",
            stability["method"],
            project,
            "GM = KB + BM - KG - FSC",
            warnings=stability["warnings"],
        ),
        "required_power": _audit(
            required_kw,
            "kW",
            propulsion["maximum"]["resistance"]["method"],
            project,
            "P_required = R_T × V / (η_prop × η_trans) × margins",
            reference="Savitsky (1964) conceptual basis; ITTC-1957 friction line",
            warnings=propulsion["maximum"]["resistance"]["warnings"],
        ),
        "range": _audit(
            fuel["range_nm"],
            "nmi",
            fuel["method"],
            project,
            "range = usable_fuel / cruise_consumption × cruise_speed",
            warnings=fuel["warnings"],
        ),
        "execution": {
            "algorithm_version": ALGORITHM_VERSION,
            "executed_at": datetime.now(UTC).isoformat(),
            "project_revision": project.revision,
        },
    }
    indicators = {
        **metrics,
        "adherence_percent": requirements["adherence_percent"],
        "mandatory_requirements_passed": requirements["mandatory_gate_passed"],
        "weight_confidence_percent": 100.0 * weights.confidence,
        "weight_margin_kg": weights.growth_margin_kg,
        "cruise_consumption_l_h": fuel["cruise_consumption_l_h"],
        "porpoising_risk": propulsion["maximum"]["resistance"]["porpoising_risk"],
        "technical_risk": min(1.0, 0.04 + 0.06 * len(warnings) + (0.25 if not hydro.converged else 0.0)),
        "maturity": "conceptual",
        "compliance_status": status,
    }
    results = {
        "weights": {**weights.model_dump(), "items": individual_weight_totals(project.weights)},
        "hydrostatics": hydro.model_dump(),
        "stability": stability,
        "resistance_curve": curve,
        "propulsion": propulsion,
        "fuel": fuel,
        "structure": structure,
        "geometry_3d": mesh_payload(project.geometry),
    }
    return EvaluationResult(
        project_id=project.project_id,
        revision=project.revision,
        status=status,
        results=results,
        requirements={
            "matrix": requirements["matrix"],
            "unresolved": requirements["unresolved"],
            "mandatory_gate_passed": requirements["mandatory_gate_passed"],
        },
        conformities=requirements["conformities"],
        non_conformities=requirements["non_conformities"],
        warnings=warnings,
        assumptions=list(dict.fromkeys(project.assumptions + [
            "Conceptual parametric hull used unless verified offsets are supplied.",
            "Demonstrative prices are synthetic and are not current quotations.",
        ])),
        margins={
            "sea_margin_fraction": project.sea_margin_fraction,
            "growth_margin_fraction": project.growth_margin_fraction,
            "power_reserve_fraction": project.power_reserve_fraction,
            "installed_power_margin_fraction": installed_kw / max(required_kw, 1.0) - 1.0,
        },
        indicators=indicators,
        traceability=traceability,
    )


def evaluate_project(project: Project, include_variants: bool = True) -> EvaluationResult:
    result = evaluate_single(project)
    if include_variants:
        from .variants import generate_and_select_variants

        variants, selected = generate_and_select_variants(project)
        result.variants = variants
        result.selected_alternatives = selected
    return result


def avaliar_projeto(projeto: Project | dict[str, Any]) -> dict[str, Any]:
    """Portuguese public entry point requested by the product specification."""
    project = projeto if isinstance(projeto, Project) else Project.model_validate(projeto)
    return evaluate_project(project).model_dump(mode="json")
