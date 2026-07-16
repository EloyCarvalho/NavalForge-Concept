import type { Evaluation, Project, RunResult } from './types'

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

export async function evaluateProject(
  project: Project,
  offlineResultUrl: string,
): Promise<RunResult> {
  if (!apiEnabled) {
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
    return {
      evaluation: await loadJson<Evaluation>(offlineResultUrl),
      mode: 'offline',
      message: `Backend não alcançado (${detail}). Exibindo demonstração offline verificada.`,
    }
  }
}
