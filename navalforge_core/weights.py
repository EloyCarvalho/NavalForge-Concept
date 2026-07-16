"""Weight, centre and loading-condition calculations."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import LoadingCondition, Project, WeightItem, WeightStatus, WeightSummary


@dataclass(frozen=True)
class MassPoint:
    description: str
    group: str
    mass_kg: float
    lcg_m: float
    tcg_m: float
    vcg_m: float
    confidence: float
    status: WeightStatus


def _condition(project: Project) -> LoadingCondition:
    for condition in project.loading_conditions:
        if condition.id == project.active_condition_id:
            return condition
    return project.loading_conditions[0]


def active_mass_points(project: Project) -> list[MassPoint]:
    """Expand the active loading condition into auditable mass points."""
    condition = _condition(project)
    allowed = set(condition.active_weight_ids)
    points: list[MassPoint] = []

    for item in project.weights:
        if not item.active or (allowed and item.id not in allowed):
            continue
        points.append(
            MassPoint(
                description=item.description,
                group=item.group,
                mass_kg=item.total_weight_kg,
                lcg_m=item.lcg_m,
                tcg_m=item.tcg_m,
                vcg_m=item.vcg_m,
                confidence=item.confidence,
                status=item.status,
            )
        )

    for tank in project.tanks:
        fill = condition.tank_fills.get(tank.id, tank.fill_fraction)
        mass = tank.capacity_m3 * fill * tank.density_kg_m3
        if mass <= 0.0:
            continue
        liquid_vcg = tank.vcg_m - tank.height_m / 2.0 + tank.height_m * fill / 2.0
        points.append(
            MassPoint(
                description=tank.description,
                group="fuel" if tank.fluid in {"diesel", "gasoline"} else "fluids",
                mass_kg=mass,
                lcg_m=tank.lcg_m,
                tcg_m=tank.tcg_m,
                vcg_m=max(0.0, liquid_vcg),
                confidence=0.9,
                status=WeightStatus.ESTIMATED,
            )
        )

    people = condition.people_count or (project.mission.crew + project.mission.passengers)
    if people:
        points.append(
            MassPoint(
                description=f"People ({people})",
                group="people",
                mass_kg=people * condition.person_mass_kg,
                lcg_m=condition.people_lcg_m or 0.52 * project.geometry.lwl_m,
                tcg_m=condition.people_tcg_m,
                vcg_m=condition.people_vcg_m,
                confidence=0.95,
                status=WeightStatus.KNOWN,
            )
        )

    cargo = condition.cargo_mass_kg or project.mission.payload_kg
    if cargo:
        points.append(
            MassPoint(
                description="Mission payload",
                group="cargo",
                mass_kg=cargo,
                lcg_m=condition.cargo_lcg_m or 0.48 * project.geometry.lwl_m,
                tcg_m=condition.cargo_tcg_m,
                vcg_m=condition.cargo_vcg_m,
                confidence=0.85,
                status=WeightStatus.ESTIMATED,
            )
        )
    return points


def calculate_weights(project: Project) -> WeightSummary:
    points = active_mass_points(project)
    total = sum(point.mass_kg for point in points)
    if total <= 0.0:
        raise ValueError("Active loading condition has zero mass")

    by_group: dict[str, float] = defaultdict(float)
    for point in points:
        by_group[point.group] += point.mass_kg

    undefined = [
        point.description
        for point in points
        if point.status == WeightStatus.UNDEFINED or point.confidence <= 0.25
    ]
    confidence = sum(point.mass_kg * point.confidence for point in points) / total
    known_total = sum(
        point.mass_kg for point in points if point.status not in {WeightStatus.MARGIN}
    )
    margin_total = total - known_total
    return WeightSummary(
        total_kg=total,
        lcg_m=sum(point.mass_kg * point.lcg_m for point in points) / total,
        tcg_m=sum(point.mass_kg * point.tcg_m for point in points) / total,
        vcg_m=sum(point.mass_kg * point.vcg_m for point in points) / total,
        confidence=confidence,
        growth_margin_kg=max(0.0, margin_total),
        by_group_kg=dict(sorted(by_group.items())),
        undefined_items=undefined,
    )


def individual_weight_totals(items: list[WeightItem]) -> list[dict[str, float | str]]:
    return [
        {
            "id": item.id,
            "description": item.description,
            "group": item.group,
            "total_weight_kg": item.total_weight_kg,
            "longitudinal_moment_kg_m": item.total_weight_kg * item.lcg_m,
            "transverse_moment_kg_m": item.total_weight_kg * item.tcg_m,
            "vertical_moment_kg_m": item.total_weight_kg * item.vcg_m,
        }
        for item in items
    ]
