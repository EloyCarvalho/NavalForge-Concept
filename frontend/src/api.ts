import type {
  Evaluation,
  Project,
  ProjectListItem,
  ProjectRevision,
  ProjectSaveResponse,
  RunResult,
} from './types'

const RAW_API_URL = import.meta.env.VITE_API_URL ?? ''
export const apiEnabled = RAW_API_URL.length > 0
export const apiBaseUrl = (RAW_API_URL === 'same-origin' ? '' : RAW_API_URL).replace(/\/$/, '')

export async function loadJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: 'no-cache' })
  if (!response.ok) throw new Error(`Não foi possível carregar ${url}: HTTP ${response.status}`)
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('json')) {
    throw new Error(`Resposta inesperada para ${url}; JSON era esperado`)
  }
  return response.json() as Promise<T>
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!apiEnabled) throw new Error('Backend não configurado nesta instalação')
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('json')) {
    throw new Error(`Resposta incompatível do backend (HTTP ${response.status})`)
  }
  const payload = await response.json() as T | { detail?: string }
  if (!response.ok) {
    const detail = 'detail' in (payload as object)
      ? String((payload as { detail?: string }).detail ?? '')
      : ''
    throw new Error(detail || `Falha no backend (HTTP ${response.status})`)
  }
  return payload as T
}

export function listProjects(): Promise<ProjectListItem[]> {
  return apiRequest<ProjectListItem[]>('/api/v1/projects')
}

export function getProject(projectId: string): Promise<Project> {
  return apiRequest<Project>(`/api/v1/projects/${encodeURIComponent(projectId)}`)
}

export async function deleteProject(projectId: string): Promise<void> {
  if (!apiEnabled) throw new Error('Backend não configurado nesta instalação')
  const response = await fetch(
    `${apiBaseUrl}/api/v1/projects/${encodeURIComponent(projectId)}`,
    { method: 'DELETE' },
  )
  if (response.status === 204) return
  let detail = `Falha ao excluir projeto (HTTP ${response.status})`
  if ((response.headers.get('content-type') ?? '').includes('json')) {
    const payload = await response.json() as { detail?: string }
    detail = payload.detail || detail
  }
  throw new Error(detail)
}

export function createProject(project: Project): Promise<ProjectSaveResponse> {
  return apiRequest<ProjectSaveResponse>('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify({ project, change_summary: 'Projeto criado pela PWA' }),
  })
}

export function saveProject(
  project: Project,
  expectedRevision: string,
  changeSummary: string,
): Promise<ProjectSaveResponse> {
  return apiRequest<ProjectSaveResponse>(
    `/api/v1/projects/${encodeURIComponent(project.project_id)}/revisions`,
    {
      method: 'POST',
      body: JSON.stringify({
        project,
        expected_revision: expectedRevision,
        change_summary: changeSummary,
      }),
    },
  )
}

export function listProjectRevisions(projectId: string): Promise<ProjectRevision[]> {
  return apiRequest<ProjectRevision[]>(
    `/api/v1/projects/${encodeURIComponent(projectId)}/revisions`,
  )
}

export function getProjectRevision(projectId: string, revisionId: string): Promise<Project> {
  return apiRequest<Project>(
    `/api/v1/projects/${encodeURIComponent(projectId)}/revisions/${encodeURIComponent(revisionId)}`,
  )
}

export async function generateReport(
  project: Project,
  evaluation: Evaluation,
  format: 'pdf' | 'docx' | 'xlsx' | 'csv' | 'json',
): Promise<Blob> {
  if (!apiEnabled) throw new Error('Backend não configurado para gerar relatórios')
  const response = await fetch(`${apiBaseUrl}/api/v1/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project, evaluation, format }),
  })
  if (!response.ok) {
    let detail = `Falha ao gerar relatório (HTTP ${response.status})`
    if ((response.headers.get('content-type') ?? '').includes('json')) {
      const payload = await response.json() as { detail?: string }
      detail = payload.detail || detail
    }
    throw new Error(detail)
  }
  return response.blob()
}

export async function evaluateProject(
  project: Project,
  offlineResultUrl?: string,
): Promise<RunResult> {
  if (!apiEnabled) {
    if (!offlineResultUrl) throw new Error('Backend indisponível para calcular este projeto')
    return {
      evaluation: await loadJson<Evaluation>(offlineResultUrl),
      mode: 'offline',
      message: 'Modo demonstrativo offline: resultado sintético previamente calculado.',
    }
  }
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project, include_variants: true }),
    })
    const contentType = response.headers.get('content-type') ?? ''
    if (!response.ok || !contentType.includes('json')) {
      throw new Error(`Backend indisponível ou incompatível (HTTP ${response.status})`)
    }
    const evaluation = (await response.json()) as Evaluation
    return {
      evaluation,
      mode: 'backend',
      message: 'Cálculo executado pelo backend auditável.',
    }
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'falha desconhecida'
    if (!offlineResultUrl) throw new Error(`Backend não alcançado (${detail})`)
    return {
      evaluation: await loadJson<Evaluation>(offlineResultUrl),
      mode: 'offline',
      message: `Backend não alcançado (${detail}). Exibindo demonstração offline verificada.`,
    }
  }
}
