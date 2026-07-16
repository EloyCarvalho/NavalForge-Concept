import type {
  Geometry,
  Mission,
  Project,
  ProjectRevision,
  Requirement,
  RequirementKind,
} from '../types'

type EditorProps = {
  project: Project
  onChange: (project: Project) => void
}

type FieldProps = {
  label: string
  value: string | number
  onChange: (value: string) => void
  type?: 'text' | 'number'
  min?: number
  max?: number
  step?: number
  readOnly?: boolean
  unit?: string
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  min,
  max,
  step,
  readOnly = false,
  unit,
}: FieldProps) {
  return (
    <label className="editor-field">
      <span>{label}</span>
      <div>
        <input
          type={type}
          value={value}
          min={min}
          max={max}
          step={step}
          readOnly={readOnly}
          onChange={(event) => onChange(event.target.value)}
        />
        {unit && <small>{unit}</small>}
      </div>
    </label>
  )
}

function SelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: Array<[string, string]>
  onChange: (value: string) => void
}) {
  return (
    <label className="editor-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, text]) => (
          <option key={optionValue} value={optionValue}>{text}</option>
        ))}
      </select>
    </label>
  )
}

const asNumber = (value: string) => Number(value)

export function ProjectEditor({ project, onChange }: EditorProps) {
  return (
    <div className="editor-stack">
      <p className="editor-help">
        Identificação do projeto persistido. O código permanece fixo para preservar a rastreabilidade.
      </p>
      <div className="editor-grid">
        <Field label="Código do projeto" value={project.project_id} readOnly onChange={() => undefined} />
        <Field label="Revisão atual" value={project.revision} readOnly onChange={() => undefined} />
        <Field
          label="Nome"
          value={project.name}
          onChange={(name) => onChange({ ...project, name })}
        />
      </div>
      <label className="editor-field editor-wide">
        <span>Descrição</span>
        <textarea
          rows={4}
          value={project.description}
          onChange={(event) => onChange({ ...project, description: event.target.value })}
        />
      </label>
    </div>
  )
}

export function MissionEditor({ project, onChange }: EditorProps) {
  const update = <K extends keyof Mission>(key: K, value: Mission[K]) => {
    onChange({ ...project, mission: { ...project.mission, [key]: value } })
  }
  return (
    <div className="editor-stack">
      <p className="editor-help">
        Defina a missão antes do recálculo. A velocidade de cruzeiro não pode exceder a máxima.
      </p>
      <div className="editor-grid">
        <Field label="Tipo de embarcação" value={project.mission.vessel_type} onChange={(value) => update('vessel_type', value)} />
        <Field label="Área de navegação" value={project.mission.navigation_area} onChange={(value) => update('navigation_area', value)} />
        <Field label="Velocidade de cruzeiro" type="number" min={1} max={80} step={0.1} unit="kn" value={project.mission.cruise_speed_kn} onChange={(value) => update('cruise_speed_kn', asNumber(value))} />
        <Field label="Velocidade máxima" type="number" min={1} max={100} step={0.1} unit="kn" value={project.mission.max_speed_kn} onChange={(value) => update('max_speed_kn', asNumber(value))} />
        <Field label="Autonomia" type="number" min={0.1} max={200} step={0.1} unit="h" value={project.mission.endurance_h} onChange={(value) => update('endurance_h', asNumber(value))} />
        <Field label="Alcance-alvo" type="number" min={1} max={5000} step={1} unit="nmi" value={project.mission.target_range_nm} onChange={(value) => update('target_range_nm', asNumber(value))} />
        <Field label="Tripulantes" type="number" min={0} max={30} step={1} value={project.mission.crew} onChange={(value) => update('crew', asNumber(value))} />
        <Field label="Passageiros" type="number" min={0} max={100} step={1} value={project.mission.passengers} onChange={(value) => update('passengers', asNumber(value))} />
        <Field label="Carga útil" type="number" min={0} max={50000} step={10} unit="kg" value={project.mission.payload_kg} onChange={(value) => update('payload_kg', asNumber(value))} />
      </div>
      <RequirementsEditor project={project} onChange={onChange} />
    </div>
  )
}

function requirementValue(value: string): Requirement['value'] {
  const cleaned = value.trim()
  if (!cleaned) return null
  const numeric = Number(cleaned.replace(',', '.'))
  return Number.isFinite(numeric) ? numeric : cleaned
}

const kindOptions: Array<[RequirementKind, string]> = [
  ['mandatory', 'Obrigatório'],
  ['desirable', 'Desejável'],
  ['constraint', 'Restrição'],
  ['score', 'Pontuação'],
  ['assumption', 'Premissa'],
  ['incomplete', 'Incompleto'],
  ['contradictory', 'Contraditório'],
  ['clarification', 'Ponto para esclarecimento'],
]

function RequirementsEditor({ project, onChange }: EditorProps) {
  const updateRequirement = (index: number, patch: Partial<Requirement>) => {
    const requirements = project.requirements.map((requirement, itemIndex) => (
      itemIndex === index ? { ...requirement, ...patch } : requirement
    ))
    onChange({ ...project, requirements })
  }
  const addRequirement = () => {
    const suffix = crypto.randomUUID().slice(0, 8).toUpperCase()
    const requirement: Requirement = {
      id: `REQ-${suffix}`,
      description: 'Novo requisito',
      category: 'mission',
      metric: null,
      operator: '>=',
      value: null,
      unit: '-',
      source: 'engenheiro responsável',
      priority: 3,
      acceptance_criterion: 'Verificar resultado calculado contra o requisito',
      verification_method: 'cálculo preliminar NavalForge',
      notes: '',
      revision: project.revision,
      kind: 'mandatory',
    }
    onChange({ ...project, requirements: [...project.requirements, requirement] })
  }
  const removeRequirement = (index: number) => {
    onChange({
      ...project,
      requirements: project.requirements.filter((_, itemIndex) => itemIndex !== index),
    })
  }

  return (
    <section className="requirements-editor">
      <div className="editor-heading">
        <div>
          <h3>Requisitos</h3>
          <p>{project.requirements.length} requisito(s) no pipeline de conformidade.</p>
        </div>
        <button type="button" className="secondary-action" onClick={addRequirement}>+ Adicionar</button>
      </div>
      <div className="requirement-list">
        {project.requirements.map((requirement, index) => (
          <details className="requirement-editor" key={requirement.id} open={index === 0}>
            <summary>
              <span>{requirement.id}</span>
              <strong>{requirement.description}</strong>
              <b className={requirement.kind === 'mandatory' ? 'mandatory' : ''}>{kindOptions.find(([value]) => value === requirement.kind)?.[1]}</b>
            </summary>
            <div className="editor-grid">
              <Field label="Descrição" value={requirement.description} onChange={(value) => updateRequirement(index, { description: value })} />
              <Field label="Categoria" value={requirement.category} onChange={(value) => updateRequirement(index, { category: value })} />
              <SelectField label="Classificação" value={requirement.kind} options={kindOptions} onChange={(value) => updateRequirement(index, { kind: value as RequirementKind })} />
              <Field label="Métrica calculada" value={requirement.metric ?? ''} onChange={(value) => updateRequirement(index, { metric: value || null })} />
              <SelectField label="Operador" value={requirement.operator} options={[[">=", 'Maior ou igual'], ['<=', 'Menor ou igual'], ['==', 'Igual'], ['in', 'Pertence à lista'], ['defined', 'Definido']]} onChange={(value) => updateRequirement(index, { operator: value as Requirement['operator'] })} />
              <Field label="Valor" value={Array.isArray(requirement.value) ? requirement.value.join(', ') : requirement.value ?? ''} onChange={(value) => updateRequirement(index, { value: requirementValue(value) })} />
              <Field label="Unidade" value={requirement.unit} onChange={(value) => updateRequirement(index, { unit: value })} />
              <Field label="Prioridade" type="number" min={1} max={5} step={1} value={requirement.priority} onChange={(value) => updateRequirement(index, { priority: asNumber(value) })} />
              <Field label="Origem" value={requirement.source} onChange={(value) => updateRequirement(index, { source: value })} />
              <Field label="Método de verificação" value={requirement.verification_method} onChange={(value) => updateRequirement(index, { verification_method: value })} />
            </div>
            <label className="editor-field editor-wide">
              <span>Critério de aceitação</span>
              <textarea rows={2} value={requirement.acceptance_criterion} onChange={(event) => updateRequirement(index, { acceptance_criterion: event.target.value })} />
            </label>
            <label className="editor-field editor-wide">
              <span>Observações</span>
              <textarea rows={2} value={requirement.notes} onChange={(event) => updateRequirement(index, { notes: event.target.value })} />
            </label>
            <button type="button" className="danger-action" onClick={() => removeRequirement(index)}>Excluir requisito</button>
          </details>
        ))}
      </div>
    </section>
  )
}

export function DimensionsEditor({ project, onChange }: EditorProps) {
  const update = <K extends keyof Geometry>(key: K, value: Geometry[K]) => {
    onChange({ ...project, geometry: { ...project.geometry, [key]: value } })
  }
  return (
    <div className="editor-stack">
      <p className="editor-help">
        Geometria paramétrica preliminar. Relações inválidas serão rejeitadas pelo backend antes do cálculo.
      </p>
      <div className="editor-grid">
        <Field label="Comprimento total" type="number" min={4.01} max={20} step={0.01} unit="m" value={project.geometry.loa_m} onChange={(value) => update('loa_m', asNumber(value))} />
        <Field label="Comprimento na linha d’água" type="number" min={3.51} max={20} step={0.01} unit="m" value={project.geometry.lwl_m} onChange={(value) => update('lwl_m', asNumber(value))} />
        <Field label="Boca máxima" type="number" min={1.01} max={6} step={0.01} unit="m" value={project.geometry.beam_m} onChange={(value) => update('beam_m', asNumber(value))} />
        <Field label="Boca no chine" type="number" min={0.81} max={5.5} step={0.01} unit="m" value={project.geometry.chine_beam_m} onChange={(value) => update('chine_beam_m', asNumber(value))} />
        <Field label="Pontal" type="number" min={0.41} max={4} step={0.01} unit="m" value={project.geometry.depth_m} onChange={(value) => update('depth_m', asNumber(value))} />
        <Field label="Calado de projeto" type="number" min={0.11} max={2} step={0.01} unit="m" value={project.geometry.design_draft_m} onChange={(value) => update('design_draft_m', asNumber(value))} />
        <Field label="Deadrise" type="number" min={5} max={35} step={0.1} unit="°" value={project.geometry.deadrise_deg} onChange={(value) => update('deadrise_deg', asNumber(value))} />
        <Field label="Flare" type="number" min={0} max={45} step={0.1} unit="°" value={project.geometry.flare_deg} onChange={(value) => update('flare_deg', asNumber(value))} />
        <Field label="Boca do espelho" type="number" min={0.51} max={5.5} step={0.01} unit="m" value={project.geometry.transom_beam_m ?? 0} onChange={(value) => update('transom_beam_m', asNumber(value))} />
        <Field label="Elevação da proa" type="number" min={0} max={2} step={0.01} unit="m" value={project.geometry.bow_rise_m} onChange={(value) => update('bow_rise_m', asNumber(value))} />
        <Field label="Número de chines" type="number" min={1} max={2} step={1} value={project.geometry.chine_count} onChange={(value) => update('chine_count', asNumber(value))} />
        <Field label="Estações" type="number" min={11} max={201} step={2} value={project.geometry.stations} onChange={(value) => update('stations', asNumber(value))} />
      </div>
    </div>
  )
}

export function ConfigurationEditor({ project, onChange }: EditorProps) {
  const updateNumber = (key: keyof Project, value: string) => {
    onChange({ ...project, [key]: asNumber(value) })
  }
  return (
    <div className="editor-stack">
      <p className="editor-help">Premissas técnicas explícitas usadas no cálculo de potência, margens e custo.</p>
      <div className="editor-grid">
        <SelectField label="Material" value={project.material} options={[["aluminum", 'Alumínio'], ['hdpe', 'PEAD'], ['composite', 'Compósito']]} onChange={(value) => onChange({ ...project, material: value })} />
        <SelectField label="Propulsão" value={project.propulsion_type} options={[["outboard", 'Motor de popa'], ['sterndrive', 'Centro-rabeta'], ['shaft', 'Eixo e hélice'], ['waterjet', 'Hidrojato']]} onChange={(value) => onChange({ ...project, propulsion_type: value })} />
        <Field label="Densidade da água" type="number" min={990} max={1035} step={1} unit="kg/m³" value={project.water_density_kg_m3} onChange={(value) => updateNumber('water_density_kg_m3', value)} />
        <Field label="Eficiência propulsiva" type="number" min={0.11} max={0.95} step={0.01} value={project.propulsive_efficiency} onChange={(value) => updateNumber('propulsive_efficiency', value)} />
        <Field label="Eficiência da transmissão" type="number" min={0.51} max={1} step={0.01} value={project.transmission_efficiency} onChange={(value) => updateNumber('transmission_efficiency', value)} />
        <Field label="Margem de mar" type="number" min={0} max={1} step={0.01} value={project.sea_margin_fraction} onChange={(value) => updateNumber('sea_margin_fraction', value)} />
        <Field label="Margem de crescimento" type="number" min={0} max={1} step={0.01} value={project.growth_margin_fraction} onChange={(value) => updateNumber('growth_margin_fraction', value)} />
        <Field label="Reserva de potência" type="number" min={0} max={1} step={0.01} value={project.power_reserve_fraction} onChange={(value) => updateNumber('power_reserve_fraction', value)} />
        <Field label="Área aerodinâmica" type="number" min={0} max={100} step={0.1} unit="m²" value={project.air_drag_area_m2} onChange={(value) => updateNumber('air_drag_area_m2', value)} />
        <Field label="Rugosidade" type="number" min={0} max={0.01} step={0.00001} unit="m" value={project.roughness_m} onChange={(value) => updateNumber('roughness_m', value)} />
        <Field label="Custo estimado demonstrativo" type="number" min={0} step={1000} unit="R$" value={project.estimated_build_cost_brl} onChange={(value) => updateNumber('estimated_build_cost_brl', value)} />
      </div>
    </div>
  )
}

export function RevisionHistory({
  revisions,
  onLoad,
}: {
  revisions: ProjectRevision[]
  onLoad: (revision: ProjectRevision) => void
}) {
  if (!revisions.length) return <p className="empty-state">O histórico será criado no primeiro salvamento.</p>
  return (
    <div className="revision-list">
      {revisions.map((revision) => (
        <article key={revision.revision_id}>
          <div>
            <strong>{revision.revision}</strong>
            <span>{revision.change_summary}</span>
            <small>{new Date(revision.created_at).toLocaleString('pt-BR')}</small>
          </div>
          <button type="button" className="secondary-action" onClick={() => onLoad(revision)}>Abrir cópia</button>
        </article>
      ))}
    </div>
  )
}
