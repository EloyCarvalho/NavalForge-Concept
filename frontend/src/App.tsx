import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  apiEnabled,
  createProject,
  deleteProject,
  evaluateProject,
  getProject,
  getProjectRevision,
  generateReport,
  listProjectRevisions,
  listProjects,
  loadJson,
  saveProject,
} from './api'
import { Dashboard } from './components/Dashboard'
import { ModuleScreen } from './components/ModuleScreen'
import type {
  DemoDescriptor,
  Evaluation,
  Project,
  ProjectListItem,
  ProjectRevision,
  RunResult,
} from './types'
import { APP_VERSION } from './version'

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const demos: DemoDescriptor[] = [
  {
    key: 'service',
    label: 'Lancha de serviço · 7 m',
    projectUrl: '/demo/nf-demo-service-7m.project.json',
    resultUrl: '/demo/nf-demo-service-7m.result.json',
  },
  {
    key: 'patrol',
    label: 'Lancha de patrulha · 10 m',
    projectUrl: '/demo/nf-demo-patrol-10m.project.json',
    resultUrl: '/demo/nf-demo-patrol-10m.result.json',
  },
  {
    key: 'rescue',
    label: 'Resgate e apoio · 12 m',
    projectUrl: '/demo/nf-demo-rescue-12m.project.json',
    resultUrl: '/demo/nf-demo-rescue-12m.result.json',
  },
]

const navigation = [
  { section: 'COMANDO', items: [['dashboard', 'Painel inicial'], ['projects', 'Projetos']] },
  { section: 'DEFINIÇÃO', items: [['mission', 'Missão e requisitos'], ['dimensions', 'Dimensões'], ['configuration', 'Configuração']] },
  { section: 'MODELO', items: [['hull', 'Casco 3D'], ['weights', 'Pesos e centros'], ['loading', 'Condições de carregamento'], ['tanks', 'Tanques']] },
  { section: 'ANÁLISES', items: [['hydrostatics', 'Hidrostática'], ['trim', 'Trim e equilíbrio'], ['stability', 'Estabilidade'], ['resistance', 'Resistência e planeio']] },
  { section: 'PROPULSÃO', items: [['power', 'Potência'], ['engines', 'Motores'], ['fuel', 'Combustível']] },
  { section: 'SÍNTESE', items: [['structure', 'Estrutura preliminar'], ['variants', 'Variantes'], ['adherence', 'Matriz de aderência'], ['reports', 'Relatórios'], ['traceability', 'Rastreabilidade'], ['settings', 'Configurações']] },
] as const

const titleByScreen = Object.fromEntries(
  navigation.flatMap((group) => group.items.map(([id, label]) => [id, label])),
) as Record<string, string>

export default function App() {
  const [selection, setSelection] = useState(() => {
    const storedSelection = localStorage.getItem('navalforge-selection')
    if (storedSelection?.startsWith('project:') || storedSelection?.startsWith('demo:')) {
      return storedSelection
    }
    const storedDemo = localStorage.getItem('navalforge-demo')
    return `demo:${demos.some((item) => item.key === storedDemo) ? storedDemo : 'service'}`
  })
  const [project, setProject] = useState<Project | null>(null)
  const [baselineProject, setBaselineProject] = useState<Project | null>(null)
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [projectSource, setProjectSource] = useState<'demo' | 'database'>('demo')
  const [savedProjects, setSavedProjects] = useState<ProjectListItem[]>([])
  const [revisions, setRevisions] = useState<ProjectRevision[]>([])
  const [dirty, setDirty] = useState(false)
  const [changeSummary, setChangeSummary] = useState('Atualização pelo aplicativo móvel')
  const [screen, setScreen] = useState('dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [runMode, setRunMode] = useState<RunResult['mode']>('offline')
  const [runMessage, setRunMessage] = useState('Carregando caso demonstrativo auditável…')
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const selectedDemoKey = selection.startsWith('demo:')
    ? selection.slice('demo:'.length) as DemoDescriptor['key']
    : 'service'
  const descriptor = useMemo(
    () => demos.find((item) => item.key === selectedDemoKey) ?? demos[0],
    [selectedDemoKey],
  )

  const refreshSavedProjects = useCallback(async () => {
    if (!apiEnabled) return
    try {
      setSavedProjects(await listProjects())
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao listar projetos salvos')
    }
  }, [])

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  useEffect(() => {
    void refreshSavedProjects()
  }, [refreshSavedProjects])

  useEffect(() => {
    if (!dirty) return
    const warnBeforeLeaving = (event: BeforeUnloadEvent) => {
      event.preventDefault()
    }
    window.addEventListener('beforeunload', warnBeforeLeaving)
    return () => window.removeEventListener('beforeunload', warnBeforeLeaving)
  }, [dirty])

  useEffect(() => {
    let cancelled = false
    setBusy(true)
    setError('')
    setProject(null)
    setEvaluation(null)

    const loadSelection = async () => {
      if (selection.startsWith('project:')) {
        const projectId = selection.slice('project:'.length)
        const [loadedProject, loadedRevisions] = await Promise.all([
          getProject(projectId),
          listProjectRevisions(projectId),
        ])
        const result = await evaluateProject(loadedProject)
        if (cancelled) return
        setProject(loadedProject)
        setBaselineProject(structuredClone(loadedProject))
        setEvaluation(result.evaluation)
        setRevisions(loadedRevisions)
        setProjectSource('database')
        setDirty(false)
        setRunMode(result.mode)
        setRunMessage(result.message)
        return
      }

      const [loadedProject, loadedEvaluation] = await Promise.all([
        loadJson<Project>(descriptor.projectUrl),
        loadJson<Evaluation>(descriptor.resultUrl),
      ])
      if (cancelled) return
      setProject(loadedProject)
      setBaselineProject(structuredClone(loadedProject))
      setEvaluation(loadedEvaluation)
      setRevisions([])
      setProjectSource('demo')
      setDirty(false)
      setRunMode('offline')
      setRunMessage(
        apiEnabled
          ? 'Resultado demonstrativo carregado. Toque em Executar projeto para realizar um novo cálculo no backend auditável.'
          : 'Modo demonstrativo offline: resultado sintético previamente calculado. Configure o backend para calcular alterações.',
      )
      localStorage.setItem('navalforge-demo', descriptor.key)
    }

    void loadSelection()
      .catch((reason: unknown) => {
        if (cancelled) return
        setError(reason instanceof Error ? reason.message : 'Falha ao carregar projeto')
        if (selection.startsWith('project:')) {
          const fallback = 'demo:service'
          localStorage.setItem('navalforge-selection', fallback)
          setSelection(fallback)
        }
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [descriptor, selection])

  const changeSelection = (value: string) => {
    if (dirty && !window.confirm('Descartar as alterações locais e abrir outro projeto?')) return
    setSuccess('')
    setSelection(value)
    localStorage.setItem('navalforge-selection', value)
  }

  const editProject = (nextProject: Project) => {
    setProject(nextProject)
    setDirty(true)
    setSuccess('')
  }

  const run = async () => {
    if (!project) return
    setBusy(true)
    setError('')
    try {
      const result = await evaluateProject(
        project,
        projectSource === 'demo' ? descriptor.resultUrl : undefined,
      )
      setEvaluation(result.evaluation)
      setRunMode(result.mode)
      setRunMessage(result.message)
      localStorage.setItem('navalforge-last-result', JSON.stringify(result.evaluation))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao executar o projeto')
    } finally {
      setBusy(false)
    }
  }

  const createEditableProject = async () => {
    if (!project || !apiEnabled) return
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const slug = project.name
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-zA-Z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, 42)
        .toUpperCase() || 'PROJETO'
      const projectId = `NF-${slug}-${Date.now().toString(36).toUpperCase()}`
      const editable: Project = {
        ...structuredClone(project),
        project_id: projectId,
        name: `${project.name} — Projeto editável`,
        revision: 'P1',
        requirements: project.requirements.map((requirement) => ({ ...requirement, revision: 'P1' })),
      }
      await createProject(editable)
      await refreshSavedProjects()
      const newSelection = `project:${projectId}`
      localStorage.setItem('navalforge-selection', newSelection)
      setSelection(newSelection)
      setSuccess('Projeto criado no Neon. A revisão P1 está preservada no histórico.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao criar projeto')
    } finally {
      setBusy(false)
    }
  }

  const saveRevision = async () => {
    if (!project || !baselineProject || projectSource !== 'database') return
    setBusy(true)
    setError('')
    setSuccess('')
    let savedRevisionLabel = ''
    try {
      const saved = await saveProject(project, baselineProject.revision, changeSummary)
      savedRevisionLabel = saved.project.revision
      setProject(saved.project)
      setBaselineProject(structuredClone(saved.project))
      setDirty(false)
      setChangeSummary('Atualização pelo aplicativo móvel')
      setSuccess(`Revisão ${saved.project.revision} salva no Neon.`)
      const [history, result] = await Promise.all([
        listProjectRevisions(saved.project.project_id),
        evaluateProject(saved.project),
      ])
      setRevisions(history)
      setEvaluation(result.evaluation)
      setRunMode(result.mode)
      setRunMessage(`Revisão ${saved.project.revision} salva e recalculada pelo backend auditável.`)
      setSuccess(`Revisão ${saved.project.revision} salva no Neon e cálculo atualizado.`)
      await refreshSavedProjects()
    } catch (reason) {
      const detail = reason instanceof Error ? reason.message : 'falha desconhecida'
      setError(
        savedRevisionLabel
          ? `${savedRevisionLabel} foi salva, mas o recálculo não terminou: ${detail}`
          : detail,
      )
    } finally {
      setBusy(false)
    }
  }

  const discardChanges = () => {
    if (!baselineProject) return
    setProject(structuredClone(baselineProject))
    setDirty(false)
    setSuccess('Alterações locais descartadas; a última revisão salva foi restaurada.')
  }

  const deleteSavedProject = async () => {
    if (!project || projectSource !== 'database') return
    const confirmed = window.confirm(
      `Excluir definitivamente ${project.name} e todo o histórico de revisões?`,
    )
    if (!confirmed) return
    setBusy(true)
    setError('')
    try {
      const deletedName = project.name
      await deleteProject(project.project_id)
      await refreshSavedProjects()
      const demoSelection = 'demo:service'
      localStorage.setItem('navalforge-selection', demoSelection)
      setSelection(demoSelection)
      setSuccess(`${deletedName} e seu histórico foram excluídos do Neon.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao excluir projeto')
    } finally {
      setBusy(false)
    }
  }

  const loadRevision = async (revision: ProjectRevision) => {
    if (!project) return
    setBusy(true)
    setError('')
    try {
      const historical = await getProjectRevision(project.project_id, revision.revision_id)
      setProject(historical)
      setDirty(true)
      setChangeSummary(`Restauração baseada na revisão ${revision.revision}`)
      setSuccess(`${revision.revision} aberta como rascunho. Salve para criar uma nova revisão sem apagar o histórico.`)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao abrir revisão')
    } finally {
      setBusy(false)
    }
  }

  const downloadReport = async (format: 'pdf' | 'docx' | 'xlsx' | 'csv' | 'json') => {
    if (!project || !evaluation) return
    if (dirty) {
      setError('Salve e recalcule o rascunho antes de gerar um relatório rastreável.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const blob = await generateReport(project, evaluation, format)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${project.project_id}-${project.revision}.${format}`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      setSuccess(`Relatório ${format.toUpperCase()} gerado para ${project.revision}.`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Falha ao gerar relatório')
    } finally {
      setBusy(false)
    }
  }

  const install = async () => {
    if (!installPrompt) return
    await installPrompt.prompt()
    await installPrompt.userChoice
    setInstallPrompt(null)
  }

  const navigate = (id: string) => {
    setScreen(id)
    setMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (!project || !evaluation) {
    return (
      <main className="loading-screen">
        <img src="/icons/icon.svg" alt="NavalForge" />
        <h1>NavalForge Concept</h1>
        <p>{error || 'Reconstruindo o Command Center…'}</p>
      </main>
    )
  }

  const reportBase = `/demo/reports/${project.project_id.toLowerCase()}`

  return (
    <div className="app-shell">
      <header className="app-header">
        <button className="menu-button" type="button" onClick={() => setMenuOpen(true)} aria-label="Abrir menu">
          <span /><span /><span />
        </button>
        <div className="header-title">
          <span className="eyebrow">COMMAND CENTER <b>v{APP_VERSION}</b></span>
          <h1>{titleByScreen[screen] ?? 'NavalForge Concept'}</h1>
        </div>
        <div className="header-actions">
          {installPrompt && <button type="button" className="install-button" onClick={install}>Instalar app</button>}
          <select value={selection} onChange={(event) => changeSelection(event.target.value)} aria-label="Selecionar projeto">
            <optgroup label="Demonstrações">
              {demos.map((demo) => <option key={demo.key} value={`demo:${demo.key}`}>{demo.label}</option>)}
            </optgroup>
            {savedProjects.length > 0 && (
              <optgroup label="Projetos salvos no Neon">
                {savedProjects.map((saved) => <option key={saved.project_id} value={`project:${saved.project_id}`}>{saved.name} · {saved.revision}</option>)}
              </optgroup>
            )}
          </select>
          <button type="button" className="run-button" disabled={busy} onClick={run}>
            {busy ? 'Calculando…' : 'Executar projeto'}
          </button>
        </div>
      </header>

      <div className="project-strip">
        <span>{project.project_id}</span>
        <span>REV {project.revision}</span>
        <b className={runMode}>{runMode === 'offline' ? 'DEMO OFFLINE' : 'BACKEND ONLINE'}</b>
        <b className={evaluation.requirements.mandatory_gate_passed ? 'pass' : 'fail'}>
          {evaluation.requirements.mandatory_gate_passed ? 'REQUISITOS COM RESSALVAS' : 'NÃO CONFORME'}
        </b>
        {dirty && <b className="draft">RASCUNHO NÃO SALVO</b>}
      </div>

      <section className="workspace-bar" aria-label="Ações do projeto">
        <div>
          <strong>{projectSource === 'demo' ? 'Modelo demonstrativo' : `${project.name} · ${baselineProject?.revision ?? project.revision}`}</strong>
          <span>{dirty ? 'Há alterações locais aguardando salvamento.' : projectSource === 'database' ? 'Revisão sincronizada com o Neon.' : 'Crie uma cópia para editar e salvar.'}</span>
        </div>
        {projectSource === 'demo' ? (
          <button type="button" className="save-action" disabled={busy || !apiEnabled} onClick={createEditableProject}>Criar projeto editável</button>
        ) : (
          <div className="workspace-buttons">
            <input
              value={changeSummary}
              onChange={(event) => setChangeSummary(event.target.value)}
              aria-label="Resumo da alteração"
              placeholder="Resumo da alteração"
            />
            <button type="button" className="secondary-action" disabled={!dirty || busy} onClick={discardChanges}>Descartar</button>
            <button type="button" className="save-action" disabled={!dirty || busy} onClick={saveRevision}>Salvar e recalcular</button>
            <button type="button" className="danger-action" disabled={busy} onClick={deleteSavedProject}>Excluir projeto</button>
          </div>
        )}
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}
      {success && <div className="success-banner" role="status">{success}</div>}

      <main className="content">
        {screen === 'dashboard' ? (
          <Dashboard project={project} evaluation={evaluation} runMode={runMode} runMessage={runMessage} />
        ) : (
          <ModuleScreen
            screen={screen}
            title={titleByScreen[screen] ?? screen}
            project={project}
            evaluation={evaluation}
            reportBase={reportBase}
            projectSource={projectSource}
            revisions={revisions}
            onProjectChange={editProject}
            onLoadRevision={loadRevision}
            onDownloadReport={downloadReport}
          />
        )}
      </main>

      <footer>
        Resultados preliminares para apoio ao engenheiro responsável; não constituem aprovação formal,
        cálculo normativo final ou substituição de software homologado.
      </footer>

      {menuOpen && (
        <div className="drawer-layer" role="presentation" onMouseDown={() => setMenuOpen(false)}>
          <aside className="navigation-drawer" role="dialog" aria-modal="true" aria-label="Navegação" onMouseDown={(event) => event.stopPropagation()}>
            <div className="drawer-brand">
              <img src="/icons/icon.svg" alt="" />
              <div><strong>NavalForge</strong><span>CONCEPT</span></div>
              <button type="button" onClick={() => setMenuOpen(false)} aria-label="Fechar menu">×</button>
            </div>
            <nav>
              {navigation.map((group) => (
                <section key={group.section}>
                  <h2>{group.section}</h2>
                  {group.items.map(([id, label]) => (
                    <button type="button" key={id} className={screen === id ? 'active' : ''} onClick={() => navigate(id)}>{label}</button>
                  ))}
                </section>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </div>
  )
}
