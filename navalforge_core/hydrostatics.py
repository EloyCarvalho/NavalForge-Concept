"""Hydrostatic integration for parametric V-bottom hulls."""

from __future__ import annotations

from math import radians, tan

import numpy as np

from .geometry import section_properties, station_table
from .models import Geometry, HydrostaticsResult


def calculate_hydrostatics(
    geometry: Geometry,
    draft_m: float,
    trim_deg: float = 0.0,
    water_density_kg_m3: float = 1025.0,
) -> HydrostaticsResult:
    """Integrate submerged sections at an arbitrarily trimmed waterplane.

    Positive trim increases forward draft. Coordinates run from transom to bow.
    """
    stations = station_table(geometry)
    xs = np.array([s.x_m for s in stations])
    slope = tan(radians(trim_deg))
    baseline_waterline = draft_m + (xs - 0.5 * geometry.lwl_m) * slope
    submerged_depths = np.maximum(
        0.0,
        baseline_waterline - np.array([s.keel_rise_m for s in stations]),
    )

    section_data = [
        section_properties(station, geometry, float(depth))
        for station, depth in zip(stations, submerged_depths, strict=True)
    ]
    areas = np.array([data[0] for data in section_data])
    vertical_centroids = np.array([data[1] + station.keel_rise_m for data, station in zip(section_data, stations, strict=True)])
    waterline_beams = np.array([data[2] for data in section_data])
    wetted_perimeters = np.array([data[3] for data in section_data])

    volume = float(np.trapezoid(areas, xs))
    waterplane = float(np.trapezoid(waterline_beams, xs))
    wetted_area = float(np.trapezoid(wetted_perimeters, xs))
    if volume <= 1e-9 or waterplane <= 1e-9:
        raise ValueError("Waterplane does not intersect the parametric hull")

    lcb = float(np.trapezoid(areas * xs, xs) / volume)
    lcf = float(np.trapezoid(waterline_beams * xs, xs) / waterplane)
    kb = float(np.trapezoid(areas * vertical_centroids, xs) / volume)
    it = float(np.trapezoid(waterline_beams**3 / 12.0, xs))
    il = float(np.trapezoid(waterline_beams * (xs - lcf) ** 2, xs))
    bmt = it / volume
    bml = il / volume

    mean_submerged = max(0.01, float(np.mean(submerged_depths)))
    max_section = max(float(np.max(areas)), 1e-9)
    displacement_kg = volume * water_density_kg_m3
    cb = volume / max(geometry.lwl_m * geometry.beam_m * mean_submerged, 1e-9)
    cp = volume / max(max_section * geometry.lwl_m, 1e-9)
    cwp = waterplane / max(geometry.lwl_m * geometry.beam_m, 1e-9)
    cm = max_section / max(geometry.beam_m * mean_submerged, 1e-9)
    tpc = water_density_kg_m3 * waterplane * 0.01 / 1000.0
    gml = kb + bml
    mtc = (displacement_kg / 1000.0) * gml * 0.01 / geometry.lwl_m

    stern_draft = max(0.0, float(baseline_waterline[0]))
    bow_draft = max(0.0, float(baseline_waterline[-1] - stations[-1].keel_rise_m))
    freeboard = geometry.depth_m - max(stern_draft, bow_draft, draft_m)
    return HydrostaticsResult(
        draft_m=draft_m,
        trim_deg=trim_deg,
        volume_m3=volume,
        displacement_kg=displacement_kg,
        waterplane_area_m2=waterplane,
        wetted_area_m2=wetted_area,
        lcb_m=lcb,
        lcf_m=lcf,
        kb_m=kb,
        bmt_m=bmt,
        bml_m=bml,
        kmt_m=kb + bmt,
        kml_m=kb + bml,
        cb=max(0.0, min(cb, 1.5)),
        cp=max(0.0, min(cp, 1.5)),
        cwp=max(0.0, min(cwp, 1.5)),
        cm=max(0.0, min(cm, 1.5)),
        tpc_t_per_cm=tpc,
        mtc_t_m_per_cm=mtc,
        bow_draft_m=bow_draft,
        stern_draft_m=stern_draft,
        freeboard_m=freeboard,
        method="horizontal strips + longitudinal trapezoidal integration",
    )


def hydrostatic_table(
    geometry: Geometry,
    drafts_m: list[float],
    density_kg_m3: float = 1025.0,
) -> list[dict[str, float]]:
    return [
        calculate_hydrostatics(geometry, draft, 0.0, density_kg_m3).model_dump()
        for draft in drafts_m
    ]
