import type { ReactNode } from 'react'
import type { Evaluation, Project, ProjectRevision } from '../types'
import { APP_VERSION } from '../version'
import { HullScene } from './HullScene'
import {
  ConfigurationEditor,
  DimensionsEditor,
  MissionEditor,
  ProjectEditor,
  RevisionHistory,
} from './ProjectEditors'

type Props = {
  screen: string
  title: string
  project: Project
  evaluation: Evaluation
  reportBase: string
  projectSource: 'demo' | 'database'
  revisions: ProjectRevision[]
  onProjectChange: (project: Project) => void
  onLoadRevision: (revision: ProjectRevision) => void
  onDownloadReport: (format: 'pdf' | 'docx' | 'xlsx' | 'csv' | 'json') => void
}

function format(value: unknown): string {
  if (typeof value === 'number') {
    return value.toLocaleString('pt-BR', { maximumFractionDigits: 3 })
  }
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não'
  if (value === null || value === undefined) return '—'
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function KeyValue({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="key-value-grid">
      {Object.entries(data).map(([key, value]) => (
        <div key={key}>
          <span>{key.replaceAll('_', ' ')}</span>
          <strong>{format(value)}</strong>
        </div>
      ))}
    </div>
  )
}

function DataTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  const headers = Array.from(new Set(rows.flatMap((row) => Object.keys(row)))).slice(0, 10)
  if (!rows.length) return <p className="empty-state">Nenhum registro disponível.</p>
  return (
    <div className="table-scroll">
      <table>
        <thead><tr>{headers.map((header) => <th key={header}>{header.replaceAll('_', ' ')}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={String(row.id ?? row.variant_id ?? index)}>
              {headers.map((header) => <td key={header}>{format(row[header])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ModuleScreen({
  screen,
  title,
  project,
  evaluation,
  reportBase,
  projectSource,
  revisions,
  onProjectChange,
  onLoadRevision,
  onDownloadReport,
}: Props) {
  let content: ReactNode
  const hydro = evaluation.results.hydrostatics
  const weights = evaluation.results.weights

  switch (screen) {
    case 'projects':
      content = (
        <>
          <div className={`persistence-notice ${projectSource}`}>
            <strong>{projectSource === 'demo' ? 'MODELO DEMONSTRATIVO' : 'PROJETO PERSISTIDO NO NEON'}</strong>
            <span>
              {projectSource === 'demo'
                ? 'Edite os campos e crie uma cópia para começar seu projeto. Não informe dados confidenciais nesta versão demonstrativa.'
                : 'As alterações ficam locais até você salvar uma nova revisão.'}
            </span>
          </div>
          <ProjectEditor project={project} onChange={onProjectChange} />
          {projectSource === 'database' && (
            <>
              <h3>Histórico de revisões</h3>
              <RevisionHistory revisions={revisions} onLoad={onLoadRevision} />
            </>
          )}
        </>
      )
      break
    case 'mission':
      content = <MissionEditor project={project} onChange={onProjectChange} />
      break
    case 'dimensions':
      content = <DimensionsEditor project={project} onChange={onProjectChange} />
      break
    case 'configuration':
      content = <ConfigurationEditor project={project} onChange={onProjectChange} />
      break
    case 'hull':
      content = <HullScene project={project} evaluation={evaluation} />
      break
    case 'weights':
      content = <><KeyValue data={{ total_kg: weights.total_kg, lcg_m: weights.lcg_m, tcg_m: weights.tcg_m, vcg_m: weights.vcg_m, confidence: weights.confidence }} /><h3>Itens de peso</h3><DataTable rows={weights.items} /></>
      break
    case 'loading':
      content = <DataTable rows={project.weights.map((item) => item as Record<string, unknown>)} />
      break
    case 'tanks':
      content = <DataTable rows={(evaluation.results.stability.tanks as { tanks?: Array<Record<string, unknown>> } | undefined)?.tanks ?? project.tanks} />
      break
    case 'hydrostatics':
    case 'trim':
      content = <KeyValue data={hydro} />
      break
    case 'stability':
      content = <KeyValue data={Object.fromEntries(Object.entries(evaluation.results.stability).filter(([, value]) => !Array.isArray(value) && typeof value !== 'object'))} />
      break
    case 'resistance':
      content = <DataTable rows={evaluation.results.resistance_curve as Array<Record<string, unknown>>} />
      break
    case 'power':
      content = <KeyValue data={{ required_installed_power_kw: evaluation.indicators.required_power_kw, installed_power_kw: evaluation.indicators.installed_power_kw, power_margin: evaluation.margins.installed_power_margin_fraction }} />
      break
    case 'engines':
      content = <DataTable rows={evaluation.results.propulsion.compatible_engines} />
      break
    case 'fuel':
      content = <KeyValue data={evaluation.results.fuel as Record<string, unknown>} />
      break
    case 'structure':
      content = <><KeyValue data={{ material: project.material, method: evaluation.results.structure.method, frame_spacing_m: evaluation.results.structure.frame_spacing_m, longitudinal_spacing_m: evaluation.results.structure.longitudinal_spacing_m }} /><h3>Elementos</h3><DataTable rows={(evaluation.results.structure.elements as Array<Record<string, unknown>>) ?? []} /></>
      break
    case 'variants':
      content = <DataTable rows={evaluation.variants} />
      break
    case 'adherence':
      content = <DataTable rows={evaluation.requirements.matrix} />
      break
    case 'reports':
      content = (
        <div className="download-grid">
          {(['pdf', 'docx', 'xlsx', 'csv', 'json'] as const).map((extension) => (
            projectSource === 'demo'
              ? <a key={extension} href={`${reportBase}.${extension}`} download>Baixar {extension.toUpperCase()}</a>
              : <button key={extension} type="button" onClick={() => onDownloadReport(extension)}>Gerar {extension.toUpperCase()}</button>
          ))}
        </div>
      )
      break
    case 'traceability':
      content = <DataTable rows={Object.entries(evaluation.traceability).map(([key, value]) => ({ result: key, ...value }))} />
      break
    case 'settings':
      content = <KeyValue data={{ version: APP_VERSION, algorithm: evaluation.traceability.execution?.algorithm_version, project_revision: project.revision, api_url: import.meta.env.VITE_API_URL || 'não configurada — modo offline', locale: 'pt-BR', core_units: 'SI' }} />
      break
    default:
      content = <p className="empty-state">Módulo preparado para evolução.</p>
  }

  return (
    <section className="technical-card module-screen">
      <span className="eyebrow">MÓDULO AUDITÁVEL</span>
      <h2>{title}</h2>
      {content}
    </section>
  )
}
