"""Tank capacity and free-surface correction calculations."""

from __future__ import annotations

from .models import Project


def tank_analysis(project: Project, displacement_kg: float) -> dict[str, object]:
    condition = next(
        (c for c in project.loading_conditions if c.id == project.active_condition_id),
        project.loading_conditions[0],
    )
    details: list[dict[str, float | str]] = []
    total_mass_moment_kg_m = 0.0
    for tank in project.tanks:
        fill = condition.tank_fills.get(tank.id, tank.fill_fraction)
        if 0.001 < fill < 0.999:
            inertia = (
                tank.free_surface_inertia_m4
                if tank.free_surface_inertia_m4 is not None
                else tank.length_m * tank.width_m**3 / 12.0
            )
        else:
            inertia = 0.0
        mass_moment = tank.density_kg_m3 * inertia
        correction = mass_moment / max(displacement_kg, 1.0)
        total_mass_moment_kg_m += mass_moment
        details.append(
            {
                "id": tank.id,
                "description": tank.description,
                "fill_fraction": fill,
                "capacity_l": tank.capacity_m3 * 1000.0,
                "liquid_mass_kg": tank.capacity_m3 * fill * tank.density_kg_m3,
                "free_surface_inertia_m4": inertia,
                "free_surface_mass_moment_kg_m": mass_moment,
                "gm_correction_m": correction,
            }
        )
    return {
        "tanks": details,
        "combined_mass_moment_kg_m": total_mass_moment_kg_m,
        "combined_gm_correction_m": total_mass_moment_kg_m / max(displacement_kg, 1.0),
        "method": "free-surface mass moment / displacement mass",
        "warning": "Polygonal tanks require engineer-supplied free-surface inertia for final use.",
    }
