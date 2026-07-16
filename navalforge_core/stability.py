"""Initial stability, free surface and preliminary GZ assessment."""

from __future__ import annotations

from math import atan, degrees, radians, sin

import numpy as np

from .models import HydrostaticsResult, Project, WeightSummary
from .tanks import tank_analysis


def calculate_stability(
    project: Project,
    weights: WeightSummary,
    hydro: HydrostaticsResult,
) -> dict[str, object]:
    tanks = tank_analysis(project, weights.total_kg)
    fsc = float(tanks["combined_gm_correction_m"])
    gm_uncorrected = hydro.kmt_m - weights.vcg_m
    gm_corrected = gm_uncorrected - fsc
    eccentric_angle = degrees(
        atan(weights.tcg_m / max(gm_corrected, 0.01))
    )

    downflooding_angle = 60.0
    for point in project.downflooding_points:
        y = abs(float(point.get("y_m", 0.0)))
        z = float(point.get("z_m", project.geometry.depth_m))
        vertical_clearance = z - hydro.draft_m
        if y > 0.01 and vertical_clearance > 0.0:
            downflooding_angle = min(
                downflooding_angle,
                degrees(atan(vertical_clearance / y)),
            )
    max_angle = max(10.0, min(60.0, downflooding_angle))
    angles = np.linspace(0.0, max_angle, 25)
    # Wall-sided, preliminary form correction. It is deliberately flagged.
    gz = [
        gm_corrected * sin(radians(float(angle))) * (1.0 - 0.12 * (angle / 90.0) ** 2)
        for angle in angles
    ]
    max_index = int(np.argmax(gz))
    area = float(np.trapezoid(np.array(gz), np.radians(angles)))
    sensitivity = [
        {
            "vcg_m": weights.vcg_m + delta,
            "gm_corrected_m": gm_corrected - delta,
        }
        for delta in (-0.20, -0.10, 0.0, 0.10, 0.20)
    ]
    warnings = [
        "GZ curve uses a wall-sided preliminary estimate; validate with inclined geometry before statutory use."
    ]
    if not project.downflooding_points:
        warnings.append("No engineer-defined downflooding points were provided.")
    if fsc > 0.0:
        warnings.append("Partially filled tanks present; free-surface correction applied.")
    if gm_corrected <= 0.35:
        warnings.append("Corrected GM is below the configurable preliminary screening value of 0.35 m.")

    return {
        "kb_m": hydro.kb_m,
        "bmt_m": hydro.bmt_m,
        "kmt_m": hydro.kmt_m,
        "kg_m": weights.vcg_m,
        "gm_uncorrected_m": gm_uncorrected,
        "free_surface_correction_m": fsc,
        "gm_corrected_m": gm_corrected,
        "gml_m": hydro.kml_m - weights.vcg_m,
        "eccentric_weight_angle_deg": eccentric_angle,
        "downflooding_angle_deg": downflooding_angle,
        "gz_curve": [
            {"angle_deg": float(angle), "gz_m": float(value)}
            for angle, value in zip(angles, gz, strict=True)
        ],
        "gz_max_m": float(gz[max_index]),
        "gz_max_angle_deg": float(angles[max_index]),
        "positive_range_deg": float(max_angle if min(gz) >= 0.0 else 0.0),
        "gz_area_m_rad": area,
        "vcg_sensitivity": sensitivity,
        "tanks": tanks,
        "screening_status": "pass" if gm_corrected > 0.35 else "review",
        "method": "GM=KB+BM-KG-FSC; wall-sided GZ screening",
        "warnings": warnings,
    }
