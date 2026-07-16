"""Requirement verification with an unmaskable mandatory gate."""

from __future__ import annotations

from typing import Any

from .models import Project, Requirement, RequirementKind


def _compare(actual: Any, requirement: Requirement) -> bool | None:
    expected = requirement.value
    if requirement.operator == "defined":
        return actual is not None
    if actual is None or expected is None:
        return None
    try:
        if requirement.operator == ">=":
            return float(actual) >= float(expected)
        if requirement.operator == "<=":
            return float(actual) <= float(expected)
        if requirement.operator == "==":
            if isinstance(actual, str) or isinstance(expected, str):
                return str(actual).lower() == str(expected).lower()
            return abs(float(actual) - float(expected)) <= 1e-9
        if requirement.operator == "in":
            expected_values = expected if isinstance(expected, list) else [expected]
            return str(actual).lower() in {str(value).lower() for value in expected_values}
    except (TypeError, ValueError):
        return False
    return None


def verify_requirements(
    project: Project,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    conformities: list[dict[str, Any]] = []
    non_conformities: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    weighted_total = 0.0
    weighted_pass = 0.0
    mandatory_failed = False

    for requirement in project.requirements:
        actual = metrics.get(requirement.metric or "")
        passed = _compare(actual, requirement)
        row = {
            "id": requirement.id,
            "description": requirement.description,
            "category": requirement.category,
            "kind": requirement.kind.value,
            "metric": requirement.metric,
            "operator": requirement.operator,
            "required": requirement.value,
            "actual": actual,
            "unit": requirement.unit,
            "verification_method": requirement.verification_method,
            "revision": requirement.revision,
            "passed": passed,
        }
        if requirement.kind in {
            RequirementKind.MANDATORY,
            RequirementKind.DESIRABLE,
            RequirementKind.CONSTRAINT,
            RequirementKind.SCORE,
        }:
            weighted_total += requirement.priority
            if passed is True:
                weighted_pass += requirement.priority
        if passed is True:
            conformities.append(row)
        elif passed is False:
            non_conformities.append(row)
            if requirement.kind == RequirementKind.MANDATORY:
                mandatory_failed = True
        else:
            unresolved.append(row)
            if requirement.kind == RequirementKind.MANDATORY:
                mandatory_failed = True

    adherence = 100.0 if weighted_total <= 0.0 else 100.0 * weighted_pass / weighted_total
    status = (
        "NÃO CONFORME — requisito obrigatório não atendido."
        if mandatory_failed
        else "REQUIREMENTS MET — WITH ENGINEERING RESERVATIONS"
    )
    return {
        "status": status,
        "mandatory_gate_passed": not mandatory_failed,
        "adherence_percent": adherence,
        "conformities": conformities,
        "non_conformities": non_conformities,
        "unresolved": unresolved,
        "matrix": conformities + non_conformities + unresolved,
    }
