export type Project = {
  project_id: string
  name: string
  revision: string
  description: string
  material: string
  propulsion_type: string
  mission: {
    vessel_type: string
    cruise_speed_kn: number
    max_speed_kn: number
    target_range_nm: number
    payload_kg: number
    crew: number
    passengers: number
  }
  geometry: {
    loa_m: number
    lwl_m: number
    beam_m: number
    chine_beam_m: number
    depth_m: number
    deadrise_deg: number
    design_draft_m: number
  }
  weights: Array<Record<string, unknown>>
  tanks: Array<Record<string, unknown>>
  requirements: Array<Record<string, unknown>>
  downflooding_points: Array<Record<string, unknown>>
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
