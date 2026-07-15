import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'

type Props = {
  data: Array<Record<string, unknown>>
  layout: Record<string, unknown>
  ariaLabel: string
}

const baseLayout: Record<string, unknown> = {
  autosize: true,
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(4,24,34,0.62)',
  font: { color: '#c4d5da', family: 'Inter, system-ui, sans-serif', size: 12 },
  margin: { l: 58, r: 42, t: 20, b: 52 },
  legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: 1.12 },
  xaxis: { gridcolor: '#244651', zerolinecolor: '#315864', automargin: true },
  yaxis: { gridcolor: '#244651', zerolinecolor: '#315864', automargin: true },
}

export function TechnicalPlot({ data, layout, ariaLabel }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = ref.current
    if (!element) return
    void Plotly.react(
      element,
      data,
      { ...baseLayout, ...layout },
      { responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d'] },
    )
    const observer = new ResizeObserver(() => Plotly.Plots.resize(element))
    observer.observe(element)
    return () => {
      observer.disconnect()
      Plotly.purge(element)
    }
  }, [data, layout])

  return <div ref={ref} className="technical-plot" role="img" aria-label={ariaLabel} />
}
