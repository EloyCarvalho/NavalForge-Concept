"""Parametric V-bottom hull geometry helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import radians, tan

import numpy as np

from .models import Geometry


@dataclass(frozen=True)
class Station:
    x_m: float
    chine_beam_m: float
    maximum_beam_m: float
    keel_rise_m: float


def station_table(geometry: Geometry) -> list[Station]:
    """Create stations from transom (x=0) to bow (x=LWL)."""
    xs = np.linspace(0.0, geometry.lwl_m, geometry.stations)
    result: list[Station] = []
    transom = geometry.transom_beam_m or 0.88 * geometry.chine_beam_m
    for x in xs:
        r = x / geometry.lwl_m
        if r <= 0.45:
            factor = (r / 0.45) ** 0.7
            chine = transom + (geometry.chine_beam_m - transom) * factor
        else:
            u = (r - 0.45) / 0.55
            chine = geometry.chine_beam_m * (0.06 + 0.94 * (1.0 - u**1.35))
        fullness = chine / geometry.chine_beam_m
        maximum = min(geometry.beam_m, chine + 0.15 * geometry.beam_m * fullness)
        keel_rise = geometry.bow_rise_m * r**6
        result.append(Station(float(x), float(chine), float(maximum), float(keel_rise)))
    return result


def section_width_at_height(
    station: Station,
    geometry: Geometry,
    height_above_keel_m: float,
) -> float:
    """Return full section width for a V-bottom with linear flare."""
    if height_above_keel_m <= 0.0:
        return 0.0
    beta = radians(geometry.deadrise_deg)
    chine_height = max(0.02, 0.5 * station.chine_beam_m * tan(beta))
    if height_above_keel_m <= chine_height:
        return station.chine_beam_m * height_above_keel_m / chine_height
    extra = 2.0 * (height_above_keel_m - chine_height) * tan(radians(geometry.flare_deg))
    return min(station.maximum_beam_m, station.chine_beam_m + extra)


def section_properties(
    station: Station,
    geometry: Geometry,
    submerged_depth_m: float,
    vertical_slices: int = 41,
) -> tuple[float, float, float, float]:
    """Return area, vertical centroid, waterline beam and wetted perimeter.

    The section is integrated as horizontal strips. This is robust for the
    preliminary parametric level and explicitly avoids hidden form factors.
    """
    depth = max(0.0, min(submerged_depth_m, geometry.depth_m * 1.1))
    if depth <= 1e-8:
        return 0.0, 0.0, 0.0, 0.0
    zs = np.linspace(0.0, depth, vertical_slices)
    widths = np.array([section_width_at_height(station, geometry, float(z)) for z in zs])
    area = float(np.trapezoid(widths, zs))
    centroid = float(np.trapezoid(widths * zs, zs) / max(area, 1e-12))
    wl_beam = float(widths[-1])

    beta = radians(geometry.deadrise_deg)
    chine_height = max(0.02, 0.5 * station.chine_beam_m * tan(beta))
    if depth <= chine_height:
        half_width = 0.5 * wl_beam
        wetted_perimeter = 2.0 * (half_width**2 + depth**2) ** 0.5
    else:
        bottom_half = ((0.5 * station.chine_beam_m) ** 2 + chine_height**2) ** 0.5
        side_vertical = depth - chine_height
        side_horizontal = 0.5 * max(0.0, wl_beam - station.chine_beam_m)
        wetted_perimeter = 2.0 * (bottom_half + (side_vertical**2 + side_horizontal**2) ** 0.5)
    return area, centroid, wl_beam, wetted_perimeter


def mesh_payload(geometry: Geometry, vertical_levels: int = 8) -> dict[str, list]:
    """Generate a symmetric hull surface payload consumed by the web 3D view."""
    stations = station_table(geometry)
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    levels = np.linspace(0.0, geometry.depth_m, vertical_levels)

    # Three.js coordinates: X longitudinal, Y vertical (up), Z transverse.
    for station in stations:
        for z in levels:
            width = section_width_at_height(station, geometry, float(z))
            vertices.append([station.x_m, station.keel_rise_m + float(z), -0.5 * width])
            vertices.append([station.x_m, station.keel_rise_m + float(z), 0.5 * width])

    row = vertical_levels * 2
    for i in range(len(stations) - 1):
        for j in range(vertical_levels - 1):
            for side in (0, 1):
                a = i * row + j * 2 + side
                b = (i + 1) * row + j * 2 + side
                c = (i + 1) * row + (j + 1) * 2 + side
                d = i * row + (j + 1) * 2 + side
                if side == 0:
                    faces.extend([[a, c, b], [a, d, c]])
                else:
                    faces.extend([[a, b, c], [a, c, d]])

    # Close transom with strips between port and starboard.
    for j in range(vertical_levels - 1):
        a = j * 2
        b = j * 2 + 1
        c = (j + 1) * 2 + 1
        d = (j + 1) * 2
        faces.extend([[a, b, c], [a, c, d]])
    return {"vertices": vertices, "faces": faces}
