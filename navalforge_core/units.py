"""Small explicit unit conversion helpers."""

from .constants import HP_TO_KW, KNOT_TO_M_S, M_S_TO_KNOT, NM_TO_M


def knots_to_m_s(value: float) -> float:
    return value * KNOT_TO_M_S


def m_s_to_knots(value: float) -> float:
    return value * M_S_TO_KNOT


def hp_to_kw(value: float) -> float:
    return value * HP_TO_KW


def kw_to_hp(value: float) -> float:
    return value / HP_TO_KW


def nautical_miles_to_m(value: float) -> float:
    return value * NM_TO_M


def kg_to_t(value: float) -> float:
    return value / 1000.0
