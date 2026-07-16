/// <reference types="vite/client" />

declare module 'plotly.js-dist-min' {
  type PlotData = Record<string, unknown>
  type Layout = Record<string, unknown>
  type Config = Record<string, unknown>
  const Plotly: {
    react: (element: HTMLElement, data: PlotData[], layout?: Layout, config?: Config) => Promise<void>
    purge: (element: HTMLElement) => void
    Plots: { resize: (element: HTMLElement) => void }
  }
  export default Plotly
}
