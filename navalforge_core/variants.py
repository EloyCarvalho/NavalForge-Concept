"""Variant generation and NF-ECO/BALANCED/PERFORMANCE selection."""

from __future__ import annotations

from typing import Any

from .models import Project


def _compact(result: Any, variant_id: str, changes: dict[str, float]) -> dict[str, Any]:
    return {
        "variant_id": variant_id,
        "status": result.status,
        "mandatory_gate_passed": result.indicators["mandatory_requirements_passed"],
        "adherence_percent": result.indicators["adherence_percent"],
        "displacement_kg": result.indicators["displacement_kg"],
        "speed_kn": result.indicators["max_speed_kn"],
        "required_power_kw": result.indicators["required_power_kw"],
        "installed_power_kw": result.indicators["installed_power_kw"],
        "range_nm": result.indicators["range_nm"],
        "gm_m": result.indicators["gm_m"],
        "freeboard_m": result.indicators["freeboard_m"],
        "cost_brl": result.indicators["cost_brl"],
        "technical_risk": result.indicators["technical_risk"],
        "warnings_count": len(result.warnings),
        "changes": changes,
    }


def generate_variants(project: Project) -> list[dict[str, Any]]:
    from .evaluator import evaluate_single

    variants: list[dict[str, Any]] = []
    index = 1
    for length_factor in (0.97, 1.0, 1.03):
        for deadrise_delta in (-2.0, 0.0, 2.0):
            candidate = project.model_copy(deep=True)
            candidate.project_id = f"{project.project_id}-V{index:03d}"
            candidate.geometry.loa_m *= length_factor
            candidate.geometry.lwl_m *= length_factor
            candidate.geometry.deadrise_deg = max(
                8.0, min(30.0, candidate.geometry.deadrise_deg + deadrise_delta)
            )
            beam_factor = 1.0 + 0.35 * (length_factor - 1.0)
            candidate.geometry.beam_m *= beam_factor
            candidate.geometry.chine_beam_m *= beam_factor
            if candidate.geometry.transom_beam_m:
                candidate.geometry.transom_beam_m *= beam_factor
            scale = length_factor * beam_factor
            for item in candidate.weights:
                if item.group in {"hull_structure", "deck", "superstructure"}:
                    item.unit_weight_kg *= scale
                if item.group == "propulsion":
                    item.lcg_m *= length_factor
            candidate.estimated_build_cost_brl *= 0.92 + 0.08 * scale + 0.004 * abs(deadrise_delta)
            candidate.assumptions.append(
                f"Variant changed L by {100*(length_factor-1):+.1f}% and deadrise by {deadrise_delta:+.1f} deg."
            )
            try:
                result = evaluate_single(candidate)
                variants.append(
                    _compact(
                        result,
                        candidate.project_id,
                        {
                            "length_factor": length_factor,
                            "beam_factor": beam_factor,
                            "deadrise_delta_deg": deadrise_delta,
                        },
                    )
                )
            except Exception as exc:  # A rejected candidate remains traceable.
                variants.append(
                    {
                        "variant_id": candidate.project_id,
                        "status": "REJECTED — pipeline calculation failed",
                        "mandatory_gate_passed": False,
                        "error": str(exc),
                        "changes": {
                            "length_factor": length_factor,
                            "beam_factor": beam_factor,
                            "deadrise_delta_deg": deadrise_delta,
                        },
                    }
                )
            index += 1
    return variants


def _balanced_score(item: dict[str, Any]) -> float:
    return (
        0.25 * float(item["adherence_percent"]) / 100.0
        + 0.18 * min(float(item["range_nm"]) / 250.0, 1.0)
        + 0.16 * min(float(item["speed_kn"]) / 50.0, 1.0)
        + 0.16 * min(float(item["gm_m"]) / 1.2, 1.0)
        + 0.12 * (1.0 - min(float(item["technical_risk"]), 1.0))
        + 0.13 * (1.0 / max(float(item["cost_brl"]) / 500000.0, 0.2))
    )


def _choice_payload(item: dict[str, Any], rationale: str) -> dict[str, Any]:
    return {**item, "rationale": rationale}


def select_alternatives(variants: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    eligible = [item for item in variants if item.get("mandatory_gate_passed") is True]
    if not eligible:
        return {
            "eco": {},
            "balanced": {},
            "performance": {},
            "selection_warning": {
                "status": "NÃO CONFORME — no variant passed every mandatory requirement."
            },
        }
    eco = min(eligible, key=lambda item: float(item["cost_brl"]))
    remaining = [item for item in eligible if item["variant_id"] != eco["variant_id"]] or eligible
    performance = max(
        remaining,
        key=lambda item: (
            float(item["speed_kn"]),
            float(item["range_nm"]),
            float(item["gm_m"]),
        ),
    )
    balanced_pool = [
        item for item in remaining if item["variant_id"] != performance["variant_id"]
    ] or remaining
    balanced = max(balanced_pool, key=_balanced_score)
    return {
        "eco": _choice_payload(
            eco,
            "Lowest demonstrative cost among variants passing every mandatory requirement.",
        ),
        "balanced": _choice_payload(
            balanced,
            "Highest auditable multicriteria balance of cost, performance, range, GM and risk.",
        ),
        "performance": _choice_payload(
            performance,
            "Highest combined performance and technical-margin screening among compliant variants.",
        ),
    }


def generate_and_select_variants(
    project: Project,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    variants = generate_variants(project)
    return variants, select_alternatives(variants)
