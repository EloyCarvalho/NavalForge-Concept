"""Two-degree-of-freedom displacement and longitudinal equilibrium solver."""

from __future__ import annotations

from scipy.optimize import least_squares

from .hydrostatics import calculate_hydrostatics
from .models import Geometry, HydrostaticsResult


def solve_equilibrium(
    geometry: Geometry,
    target_mass_kg: float,
    lcg_m: float,
    water_density_kg_m3: float = 1025.0,
    initial_draft_m: float | None = None,
) -> HydrostaticsResult:
    """Solve buoyancy=weight and LCB=LCG for mean draft and trim."""
    if target_mass_kg <= 0.0:
        raise ValueError("target_mass_kg must be positive")
    draft0 = initial_draft_m or geometry.design_draft_m

    def residual(vector: list[float]) -> list[float]:
        draft, trim = float(vector[0]), float(vector[1])
        try:
            hydro = calculate_hydrostatics(
                geometry,
                draft,
                trim,
                water_density_kg_m3,
            )
        except ValueError:
            return [10.0, 10.0]
        mass_error = (hydro.displacement_kg - target_mass_kg) / target_mass_kg
        centre_error = (hydro.lcb_m - lcg_m) / geometry.lwl_m
        return [mass_error, centre_error]

    solved = least_squares(
        residual,
        x0=[draft0, 0.0],
        bounds=([0.08, -8.0], [geometry.depth_m * 0.9, 8.0]),
        xtol=1e-10,
        ftol=1e-10,
        gtol=1e-10,
        max_nfev=160,
    )
    draft, trim = float(solved.x[0]), float(solved.x[1])
    result = calculate_hydrostatics(geometry, draft, trim, water_density_kg_m3)
    result.residual_mass_kg = result.displacement_kg - target_mass_kg
    result.residual_lcg_m = result.lcb_m - lcg_m
    result.converged = bool(
        solved.success
        and abs(result.residual_mass_kg) <= max(2.0, target_mass_kg * 0.002)
        and abs(result.residual_lcg_m) <= max(0.01, geometry.lwl_m * 0.002)
    )
    result.method = "bounded nonlinear least-squares: buoyancy=weight and LCB=LCG"
    return result
