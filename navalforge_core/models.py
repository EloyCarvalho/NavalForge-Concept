"""Shared, validated data contracts for all NavalForge calculations."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class RequirementKind(StrEnum):
    MANDATORY = "mandatory"
    DESIRABLE = "desirable"
    CONSTRAINT = "constraint"
    SCORE = "score"
    ASSUMPTION = "assumption"
    INCOMPLETE = "incomplete"
    CONTRADICTORY = "contradictory"
    CLARIFICATION = "clarification"


class WeightStatus(StrEnum):
    KNOWN = "known"
    ESTIMATED = "estimated"
    PROVISIONAL = "provisional"
    MARGIN = "margin"
    UNDEFINED = "undefined"


class Requirement(StrictModel):
    id: str = Field(default_factory=lambda: f"REQ-{uuid4().hex[:8].upper()}")
    description: str
    category: str
    metric: str | None = None
    operator: Literal["<=", ">=", "==", "in", "defined"] = ">="
    value: float | str | list[str] | None = None
    unit: str = "-"
    source: str = "engineer"
    priority: int = Field(default=3, ge=1, le=5)
    acceptance_criterion: str = "Verify calculated result against requirement"
    verification_method: str = "calculation"
    notes: str = ""
    revision: str = "P1"
    kind: RequirementKind = RequirementKind.MANDATORY


class Geometry(StrictModel):
    revision: str = "G1"
    model_level: Literal["parametric", "offsets"] = "parametric"
    loa_m: float = Field(gt=4.0, le=20.0)
    lwl_m: float = Field(gt=3.5, le=20.0)
    beam_m: float = Field(gt=1.0, le=6.0)
    chine_beam_m: float = Field(gt=0.8, le=5.5)
    depth_m: float = Field(gt=0.4, le=4.0)
    deadrise_deg: float = Field(ge=5.0, le=35.0)
    flare_deg: float = Field(default=12.0, ge=0.0, le=45.0)
    transom_beam_m: float | None = Field(default=None, gt=0.5, le=5.5)
    chine_count: int = Field(default=1, ge=1, le=2)
    design_draft_m: float = Field(default=0.45, gt=0.1, le=2.0)
    bow_rise_m: float = Field(default=0.35, ge=0.0, le=2.0)
    stations: int = Field(default=41, ge=11, le=201)
    offsets: list[dict[str, float]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_proportions(self) -> Geometry:
        if self.lwl_m > self.loa_m:
            raise ValueError("lwl_m cannot exceed loa_m")
        if self.chine_beam_m > self.beam_m:
            raise ValueError("chine_beam_m cannot exceed beam_m")
        if self.design_draft_m >= self.depth_m:
            raise ValueError("design_draft_m must be below depth_m")
        if self.transom_beam_m is None:
            object.__setattr__(self, "transom_beam_m", 0.88 * self.chine_beam_m)
        return self


class WeightItem(StrictModel):
    id: str = Field(default_factory=lambda: f"W-{uuid4().hex[:8].upper()}")
    description: str
    group: str
    quantity: float = Field(default=1.0, ge=0.0)
    unit_weight_kg: float = Field(ge=0.0)
    lcg_m: float
    tcg_m: float = 0.0
    vcg_m: float = Field(ge=0.0)
    source: str = "estimate"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    margin_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    revision: str = "W1"
    status: WeightStatus = WeightStatus.ESTIMATED
    active: bool = True

    @property
    def total_weight_kg(self) -> float:
        return self.quantity * self.unit_weight_kg * (1.0 + self.margin_fraction)


class Tank(StrictModel):
    id: str = Field(default_factory=lambda: f"T-{uuid4().hex[:8].upper()}")
    description: str
    fluid: Literal["diesel", "gasoline", "fresh_water", "other"] = "diesel"
    shape: Literal["rectangular", "polygonal"] = "rectangular"
    length_m: float = Field(gt=0.0)
    width_m: float = Field(gt=0.0)
    height_m: float = Field(gt=0.0)
    fill_fraction: float = Field(ge=0.0, le=1.0)
    density_kg_m3: float = Field(default=840.0, gt=100.0, le=2000.0)
    lcg_m: float
    tcg_m: float = 0.0
    vcg_m: float = Field(ge=0.0)
    unusable_fraction: float = Field(default=0.03, ge=0.0, le=0.3)
    polygon_area_m2: float | None = Field(default=None, gt=0.0)
    free_surface_inertia_m4: float | None = Field(default=None, ge=0.0)

    @property
    def capacity_m3(self) -> float:
        if self.shape == "polygonal" and self.polygon_area_m2:
            return self.polygon_area_m2 * self.length_m
        return self.length_m * self.width_m * self.height_m

    @property
    def liquid_mass_kg(self) -> float:
        return self.capacity_m3 * self.fill_fraction * self.density_kg_m3


class LoadingCondition(StrictModel):
    id: str = "LC-DEPARTURE"
    name: str = "Departure"
    active_weight_ids: list[str] = Field(default_factory=list)
    tank_fills: dict[str, float] = Field(default_factory=dict)
    people_count: int = Field(default=0, ge=0, le=100)
    person_mass_kg: float = Field(default=85.0, gt=30.0, le=180.0)
    people_lcg_m: float | None = None
    people_tcg_m: float = 0.0
    people_vcg_m: float = 1.0
    cargo_mass_kg: float = Field(default=0.0, ge=0.0)
    cargo_lcg_m: float | None = None
    cargo_tcg_m: float = 0.0
    cargo_vcg_m: float = 0.7
    revision: str = "LC1"


class Mission(StrictModel):
    vessel_type: str = "service"
    navigation_area: str = "coastal"
    cruise_speed_kn: float = Field(gt=0.0, le=80.0)
    max_speed_kn: float = Field(gt=0.0, le=100.0)
    endurance_h: float = Field(default=4.0, gt=0.0, le=200.0)
    target_range_nm: float = Field(default=80.0, gt=0.0, le=5000.0)
    crew: int = Field(default=2, ge=0, le=30)
    passengers: int = Field(default=4, ge=0, le=100)
    payload_kg: float = Field(default=300.0, ge=0.0, le=50000.0)

    @model_validator(mode="after")
    def validate_speeds(self) -> Mission:
        if self.cruise_speed_kn > self.max_speed_kn:
            raise ValueError("cruise_speed_kn cannot exceed max_speed_kn")
        return self


class Project(StrictModel):
    project_id: str
    name: str
    revision: str = "P1"
    description: str = ""
    material: Literal["aluminum", "hdpe", "composite"] = "aluminum"
    propulsion_type: Literal["outboard", "sterndrive", "shaft", "waterjet"] = "outboard"
    water_density_kg_m3: float = Field(default=1025.0, ge=990.0, le=1035.0)
    mission: Mission
    geometry: Geometry
    weights: list[WeightItem]
    tanks: list[Tank] = Field(default_factory=list)
    loading_conditions: list[LoadingCondition] = Field(default_factory=lambda: [LoadingCondition()])
    active_condition_id: str = "LC-DEPARTURE"
    requirements: list[Requirement] = Field(default_factory=list)
    downflooding_points: list[dict[str, float | str]] = Field(default_factory=list)
    propulsive_efficiency: float = Field(default=0.58, gt=0.1, le=0.95)
    transmission_efficiency: float = Field(default=0.97, gt=0.5, le=1.0)
    sea_margin_fraction: float = Field(default=0.15, ge=0.0, le=1.0)
    growth_margin_fraction: float = Field(default=0.10, ge=0.0, le=1.0)
    power_reserve_fraction: float = Field(default=0.10, ge=0.0, le=1.0)
    air_drag_area_m2: float = Field(default=3.0, ge=0.0, le=100.0)
    roughness_m: float = Field(default=0.00015, ge=0.0, le=0.01)
    estimated_build_cost_brl: float = Field(default=500000.0, ge=0.0)
    assumptions: list[str] = Field(default_factory=list)


class AuditResult(StrictModel):
    calculation_id: str = Field(default_factory=lambda: f"CALC-{uuid4().hex.upper()}")
    value: float | int | str | bool | list[Any] | dict[str, Any] | None
    unit: str = "-"
    method: str
    equation: str = ""
    reference: str = ""
    loading_condition: str = ""
    geometry_revision: str = ""
    weight_revision: str = ""
    algorithm_version: str = "navalforge-core-0.1.5"
    inputs: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    compliance: str = "informative"
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WeightSummary(StrictModel):
    total_kg: float
    lcg_m: float
    tcg_m: float
    vcg_m: float
    confidence: float
    growth_margin_kg: float
    by_group_kg: dict[str, float]
    undefined_items: list[str]


class HydrostaticsResult(StrictModel):
    draft_m: float
    trim_deg: float
    volume_m3: float
    displacement_kg: float
    waterplane_area_m2: float
    wetted_area_m2: float
    lcb_m: float
    lcf_m: float
    kb_m: float
    bmt_m: float
    bml_m: float
    kmt_m: float
    kml_m: float
    cb: float
    cp: float
    cwp: float
    cm: float
    tpc_t_per_cm: float
    mtc_t_m_per_cm: float
    bow_draft_m: float
    stern_draft_m: float
    freeboard_m: float
    residual_mass_kg: float = 0.0
    residual_lcg_m: float = 0.0
    converged: bool = True
    method: str = "sectional numerical integration"


class EvaluationResult(StrictModel):
    project_id: str
    revision: str
    status: str
    results: dict[str, Any]
    requirements: dict[str, Any]
    conformities: list[dict[str, Any]]
    non_conformities: list[dict[str, Any]]
    warnings: list[str]
    assumptions: list[str]
    margins: dict[str, float]
    indicators: dict[str, Any]
    traceability: dict[str, Any]
    variants: list[dict[str, Any]] = Field(default_factory=list)
    selected_alternatives: dict[str, dict[str, Any]] = Field(default_factory=dict)
