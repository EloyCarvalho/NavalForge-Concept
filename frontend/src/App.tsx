import { useEffect, useMemo, useState } from 'react'
import { evaluateProject, loadJson } from './api'
import { Dashboard } from './components/Dashboard'
import { ModuleScreen } from './components/ModuleScreen'
import type { DemoDescriptor, Evaluation, Project, RunResult } from './types'

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
  const [selectedKey, setSelectedKey] = useState<DemoDescriptor['key']>(() => {
    const stored = localStorage.getItem('navalforge-demo')
    return demos.some((item) => item.key === stored) ? (stored as DemoDescriptor['key']) : 'service'
  })
  const [project, setProject] = useState<Project | null>(null)
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [screen, setScreen] = useState('dashboard')
  const [menuOpen, setMenuOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [runMode, setRunMode] = useState<RunResult['mode']>('offline')
  const [runMessage, setRunMessage] = useState('Carregando caso demonstrativo auditável…')
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const descriptor = useMemo(
    () => demos.find((item) => item.key === selectedKey) ?? demos[0],
    [selectedKey],
  )

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  useEffect(() => {
    let cancelled = false
    setBusy(true)
    setError('')
    Promise.all([
      loadJson<Project>(descriptor.projectUrl),
      loadJson<Evaluation>(descriptor.resultUrl),
    ])
      .then(([loadedProject, loadedEvaluation]) => {
        if (cancelled) return
        setProject(loadedProject)
        setEvaluation(loadedEvaluation)
        setRunMode('offline')
        setRunMessage('Modo demonstrativo offline: resultado sintético previamente calculado. Configure o backend para calcular alterações.')
        localStorage.setItem('navalforge-demo', descriptor.key)
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : 'Falha ao carregar demonstração')
      })
      .finally(() => {
        if (!cancelled) setBusy(false)
      })
    return () => {
      cancelled = true
    }
  }, [descriptor])

  const run = async () => {
    if (!project) return
    setBusy(true)
    setError('')
    try {
      const result = await evaluateProject(project, descriptor.resultUrl)
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
          <span className="eyebrow">COMMAND CENTER <b>v0.1.5</b></span>
          <h1>{titleByScreen[screen] ?? 'NavalForge Concept'}</h1>
        </div>
        <div className="header-actions">
          {installPrompt && <button type="button" className="install-button" onClick={install}>Instalar app</button>}
          <select value={selectedKey} onChange={(event) => setSelectedKey(event.target.value as DemoDescriptor['key'])} aria-label="Projeto demonstrativo">
            {demos.map((demo) => <option key={demo.key} value={demo.key}>{demo.label}</option>)}
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
          {evaluation.requirements.mandatory_gate_passed ? 'CONDICIONAL' : 'NÃO CONFORME'}
        </b>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

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
