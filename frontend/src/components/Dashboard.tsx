import { useMemo } from 'react'
import type { Evaluation, Project, RunResult } from '../types'
import { HullScene } from './HullScene'
import { TechnicalPlot } from './TechnicalPlot'

type Props = {
  project: Project
  evaluation: Evaluation
  runMode: RunResult['mode']
  runMessage: string
}

function number(value: unknown): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function decimal(value: unknown, digits = 2): string {
  return number(value).toLocaleString('pt-BR', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function currency(value: unknown): string {
  return number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  })
}

export function Dashboard({ project, evaluation, runMode, runMessage }: Props) {
  const indicators = evaluation.indicators
  const curve = evaluation.results.resistance_curve
  const resistanceData = useMemo(
    () => [
      {
        x: curve.map((point) => number(point.speed_kn)),
        y: curve.map((point) => number(point.total_resistance_n) / 1000),
        name: 'R total (kN)',
        mode: 'lines+markers',
        line: { color: '#46d3e2', width: 3 },
        marker: { size: 7 },
        type: 'scatter',
      },
      {
        x: curve.map((point) => number(point.speed_kn)),
        y: curve.map((point) => number(point.effective_power_kw)),
        name: 'PE (kW)',
        mode: 'lines',
        line: { color: '#ffb547', width: 3 },
        type: 'scatter',
        yaxis: 'y2',
      },
    ],
    [curve],
  )
  const resistanceLayout = useMemo(
    () => ({
      xaxis: { title: 'Velocidade (kn)', gridcolor: '#244651' },
      yaxis: { title: 'Resistência (kN)', gridcolor: '#244651' },
      yaxis2: { title: 'Potência efetiva (kW)', overlaying: 'y', side: 'right', showgrid: false },
    }),
    [],
  )
  const gz = evaluation.results.stability.gz_curve
  const gzData = useMemo(
    () => [
      {
        x: gz.map((point) => point.angle_deg),
        y: gz.map((point) => point.gz_m),
        name: 'GZ preliminar',
        mode: 'lines',
        fill: 'tozeroy',
        line: { color: '#64dda5', width: 3 },
        fillcolor: 'rgba(50, 190, 132, .42)',
        type: 'scatter',
      },
    ],
    [gz],
  )
  const gzLayout = useMemo(
    () => ({
      xaxis: { title: 'Ângulo (°)', gridcolor: '#244651' },
      yaxis: { title: 'GZ (m)', gridcolor: '#244651', rangemode: 'tozero' },
      showlegend: false,
    }),
    [],
  )

  const cards = [
    ['ADERÊNCIA', decimal(indicators.adherence_percent, 0), '%'],
    ['DESLOCAMENTO', decimal(indicators.displacement_kg), 'kg'],
    ['VELOCIDADE', decimal(indicators.max_speed_kn), 'kn'],
    ['POTÊNCIA REQUERIDA', decimal(indicators.required_power_kw), 'kW'],
    ['ALCANCE', decimal(indicators.range_nm), 'nmi'],
    ['GM CORRIGIDO', decimal(indicators.gm_m), 'm'],
    ['BORDA LIVRE', decimal(indicators.freeboard_m), 'm'],
    ['RISCO RELATIVO', decimal(indicators.technical_risk), ''],
  ]

  return (
    <>
      <section className={`mode-notice ${runMode}`}>
        <strong>{runMode === 'offline' ? 'DEMO OFFLINE' : 'BACKEND ONLINE'}</strong>
        <span>{runMessage}</span>
      </section>

      <section className="indicator-grid" aria-label="Indicadores principais">
        {cards.map(([label, value, unit]) => (
          <article className="indicator-card" key={label}>
            <span>{label}</span>
            <strong>
              {value} <small>{unit}</small>
            </strong>
          </article>
        ))}
      </section>

      <section className="technical-card hull-card">
        <h2>Casco paramétrico preliminar</h2>
        <HullScene project={project} evaluation={evaluation} />
      </section>

      <section className="technical-card gate-card">
        <h2>Gate obrigatório</h2>
        <div className={evaluation.requirements.mandatory_gate_passed ? 'gate pass' : 'gate fail'}>
          {evaluation.requirements.mandatory_gate_passed
            ? 'REQUISITOS ATENDIDOS — COM RESSALVAS'
            : 'NÃO CONFORME — REQUISITO OBRIGATÓRIO NÃO ATENDIDO'}
        </div>
        <p>{decimal(indicators.adherence_percent, 1)}% de aderência ponderada</p>
        <p>{evaluation.warnings.length} alertas ativos</p>
        {evaluation.warnings.length > 0 && (
          <details>
            <summary>Ver ressalvas técnicas</summary>
            <ul>
              {evaluation.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <section className="technical-card">
        <h2>Resistência e potência</h2>
        <TechnicalPlot
          data={resistanceData}
          layout={resistanceLayout}
          ariaLabel="Curva preliminar de resistência e potência"
        />
      </section>

      <section className="technical-card">
        <h2>Estabilidade preliminar</h2>
        <TechnicalPlot data={gzData} layout={gzLayout} ariaLabel="Curva GZ preliminar" />
      </section>

      <section className="alternatives-grid">
        {(['eco', 'balanced', 'performance'] as const).map((key) => {
          const alternative = evaluation.selected_alternatives[key]
          if (!alternative?.variant_id) return null
          return (
            <article className="technical-card alternative" key={key}>
              <span className="eyebrow">NF-{key.toUpperCase()}</span>
              <h2>{alternative.variant_id}</h2>
              <p>{alternative.rationale}</p>
              <div className="alternative-metrics">
                <div><span>VELOCIDADE</span><strong>{decimal(alternative.speed_kn)} <small>kn</small></strong></div>
                <div><span>ALCANCE</span><strong>{decimal(alternative.range_nm)} <small>nmi</small></strong></div>
                <div><span>GM</span><strong>{decimal(alternative.gm_m)} <small>m</small></strong></div>
                <div><span>CUSTO DEMO</span><strong>{currency(alternative.cost_brl)}</strong></div>
              </div>
            </article>
          )
        })}
      </section>
    </>
  )
}
