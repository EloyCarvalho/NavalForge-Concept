export type RequirementKind =
  | 'mandatory'
  | 'desirable'
  | 'constraint'
  | 'score'
  | 'assumption'
  | 'incomplete'
  | 'contradictory'
  | 'clarification'

export type Requirement = {
  id: string
  description: string
  category: string
  metric: string | null
  operator: '<=' | '>=' | '==' | 'in' | 'defined'
  value: number | string | string[] | null
  unit: string
  source: string
  priority: number
  acceptance_criterion: string
  verification_method: string
  notes: string
  revision: string
  kind: RequirementKind
}

export type Mission = {
  vessel_type: string
  navigation_area: string
  cruise_speed_kn: number
  max_speed_kn: number
  endurance_h: number
  target_range_nm: number
  payload_kg: number
  crew: number
  passengers: number
}

export type Geometry = {
  revision: string
  model_level: 'parametric' | 'offsets'
  loa_m: number
  lwl_m: number
  beam_m: number
  chine_beam_m: number
  depth_m: number
  deadrise_deg: number
  flare_deg: number
  transom_beam_m: number | null
  chine_count: number
  design_draft_m: number
  bow_rise_m: number
  stations: number
  offsets: Array<Record<string, number>>
}

export type Project = {
  project_id: string
  name: string
  revision: string
  description: string
  material: string
  propulsion_type: string
  water_density_kg_m3: number
  mission: Mission
  geometry: Geometry
  weights: Array<Record<string, unknown>>
  tanks: Array<Record<string, unknown>>
  loading_conditions: Array<Record<string, unknown>>
  active_condition_id: string
  requirements: Requirement[]
  downflooding_points: Array<Record<string, unknown>>
  propulsive_efficiency: number
  transmission_efficiency: number
  sea_margin_fraction: number
  growth_margin_fraction: number
  power_reserve_fraction: number
  air_drag_area_m2: number
  roughness_m: number
  estimated_build_cost_brl: number
  assumptions: string[]
}

export type ProjectListItem = {
  project_id: string
  name: string
  revision: string
  source: string
  updated_at: string | null
}

export type ProjectRevision = {
  revision_id: string
  project_id: string
  revision: string
  change_summary: string
  created_at: string
}

export type ProjectSaveResponse = {
  project: Project
  revision: ProjectRevision
}

export type Alternative = {
  variant_id: string
  rationale: string
  speed_kn: number
  range_nm: number
  gm_m: number
  cost_brl: number
  technical_risk: number
}

export type Evaluation = {
  project_id: string
  revision: string
  status: string
  results: {
    weights: {
      total_kg: number
      lcg_m: number
      tcg_m: number
      vcg_m: number
      confidence: number
      by_group_kg: Record<string, number>
      items: Array<Record<string, unknown>>
    }
    hydrostatics: Record<string, number | string | boolean>
    stability: {
      gm_corrected_m: number
      free_surface_correction_m: number
      gz_curve: Array<{ angle_deg: number; gz_m: number }>
      warnings: string[]
      [key: string]: unknown
    }
    resistance_curve: Array<Record<string, number | string | string[]>>
    propulsion: {
      maximum: { power: { required_installed_power_kw: number } }
      compatible_engines: Array<Record<string, unknown>>
      selected_engine: Record<string, unknown> | null
      warnings: string[]
    }
    fuel: Record<string, number | string | string[]>
    structure: Record<string, unknown>
    geometry_3d: { vertices: number[][]; faces: number[][] }
  }
  requirements: {
    matrix: Array<Record<string, unknown>>
    unresolved: Array<Record<string, unknown>>
    mandatory_gate_passed: boolean
  }
  conformities: Array<Record<string, unknown>>
  non_conformities: Array<Record<string, unknown>>
  warnings: string[]
  assumptions: string[]
  margins: Record<string, number>
  indicators: Record<string, number | string | boolean>
  traceability: Record<string, Record<string, unknown>>
  variants: Array<Record<string, unknown>>
  selected_alternatives: {
    eco?: Alternative
    balanced?: Alternative
    performance?: Alternative
  }
}

export type DemoDescriptor = {
  key: 'service' | 'patrol' | 'rescue'
  label: string
  projectUrl: string
  resultUrl: string
}

export type RunResult = {
  evaluation: Evaluation
  mode: 'backend' | 'offline'
  message: string
}
