import { Fragment, useEffect, useRef, useState, ReactNode } from 'react'
import cytoscape, { Core } from 'cytoscape'
import { Maximize2, RotateCcw, ZoomIn, ZoomOut, AlertTriangle, Loader2 } from 'lucide-react'
import { useTheme } from './theme'
import type { Graph, GNode, GEdge } from './api'

export const COLORS: Record<string, string> = { Medicine: '#F26B4F', Batch: '#80B8CC', Organization: '#7B93F0', Location: '#7CCB92',
  Shipment: '#E8B84A', Pharmacy: '#C58BE0', Recall: '#E5484D', TraceabilityEvent: '#9AA7B5' }
const SHAPES: Record<string, string> = { Medicine: 'round-rectangle', Batch: 'rectangle', Organization: 'hexagon', Location: 'diamond',
  Shipment: 'round-tag', Pharmacy: 'star', Recall: 'octagon', TraceabilityEvent: 'ellipse' }
const css = (n: string) => `rgb(${getComputedStyle(document.documentElement).getPropertyValue('--' + n).trim().split(/\s+/).join(',')})`
const reduce = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

function styles(): cytoscape.StylesheetJson {
  return [
    { selector: 'node', style: { 'background-color': 'data(color)', shape: 'data(shape)' as any, label: 'data(name)', 'font-size': 9, color: css('ink'),
      'text-valign': 'bottom', 'text-margin-y': 4, 'text-wrap': 'ellipsis', 'text-max-width': '84px', width: 26, height: 26,
      'border-width': 2, 'border-color': css('line'), 'min-zoomed-font-size': 6 } },
    { selector: 'edge', style: { 'curve-style': 'bezier', 'target-arrow-shape': 'triangle', 'line-color': css('mute'), 'target-arrow-color': css('mute'),
      width: 1.1, label: 'data(type)', 'font-size': 7, color: css('mute'), 'text-rotation': 'autorotate', 'min-zoomed-font-size': 8, opacity: 0.8 } },
    { selector: 'node:selected', style: { 'border-color': css('coral'), 'border-width': 4 } },
    { selector: 'edge:selected', style: { 'line-color': css('coral'), 'target-arrow-color': css('coral'), width: 3 } },
    { selector: '.dim', style: { opacity: 0.12 } },
    { selector: 'node.hl', style: { 'border-color': css('coral'), 'border-width': 4 } },
    { selector: 'edge.hl', style: { 'line-color': css('coral'), 'target-arrow-color': css('coral'), width: 3, opacity: 1 } },
  ] as any
}

export function GraphView({ graph, highlight, selectedId, hiddenLabels, hiddenRels, onNode, onEdge, onExpand, height = 460 }: {
  graph?: Graph; highlight?: string[]; selectedId?: string | null; hiddenLabels?: string[]; hiddenRels?: string[]
  onNode?: (n: GNode) => void; onEdge?: (e: GEdge) => void; onExpand?: (n: GNode) => void; height?: number | string }) {
  const el = useRef<HTMLDivElement>(null); const cy = useRef<Core | null>(null)
  const cb = useRef({ onNode, onEdge, onExpand }); cb.current = { onNode, onEdge, onExpand }
  const lookup = useRef<{ n: Map<string, GNode>; e: Map<string, GEdge> }>({ n: new Map(), e: new Map() })
  const { theme } = useTheme(); const [tip, setTip] = useState<{ x: number; y: number; n: GNode } | null>(null)

  useEffect(() => {
    const c = cytoscape({ container: el.current, style: styles(), wheelSensitivity: 0.3, minZoom: 0.15, maxZoom: 3 }); cy.current = c
    c.on('tap', 'node', e => { const n = lookup.current.n.get(e.target.id()); n && cb.current.onNode?.(n) })
    c.on('dbltap', 'node', e => { const n = lookup.current.n.get(e.target.id()); n && cb.current.onExpand?.(n) })
    c.on('tap', 'edge', e => { const x = lookup.current.e.get(e.target.id()); x && cb.current.onEdge?.(x) })
    c.on('mouseover', 'node', e => { const n = lookup.current.n.get(e.target.id()); const p = e.renderedPosition; n && setTip({ x: p.x, y: p.y, n }) })
    c.on('mouseout', 'node', () => setTip(null)); c.on('drag pan zoom', () => setTip(null))
    return () => c.destroy()
  }, [])
  useEffect(() => { cy.current?.style(styles() as any) }, [theme])
  useEffect(() => {
    const c = cy.current; if (!c || !graph) return
    lookup.current = { n: new Map(graph.nodes.map(n => [n.id, n])), e: new Map(graph.edges.map(e => [e.id, e])) }
    const have = new Set(c.elements().map(x => x.id())); const fresh = graph.nodes.some(n => !have.has(n.id)) || graph.edges.some(e => !have.has(e.id))
    const keep = new Set([...graph.nodes.map(n => n.id), ...graph.edges.map(e => e.id)]); c.elements().filter(x => !keep.has(x.id())).remove()
    c.add([...graph.nodes.filter(n => !have.has(n.id)).map(n => ({ group: 'nodes' as const, data: { id: n.id, name: n.name, color: COLORS[n.label] ?? '#999', shape: SHAPES[n.label] ?? 'ellipse', label: n.label } })),
      ...graph.edges.filter(e => !have.has(e.id)).map(e => ({ group: 'edges' as const, data: { id: e.id, source: e.source, target: e.target, type: e.type } }))])
    if (fresh) c.layout({ name: 'cose', animate: !reduce(), animationDuration: 400, fit: true, padding: 30, nodeRepulsion: () => 12000, idealEdgeLength: () => 95, nodeOverlap: 20 } as any).run()
  }, [graph])
  useEffect(() => {
    const c = cy.current; if (!c) return
    c.batch(() => {
      c.elements().removeClass('dim hl').style('display', 'element')
      c.nodes().filter(n => !!hiddenLabels?.includes(n.data('label'))).style('display', 'none')
      c.edges().filter(e => !!hiddenRels?.includes(e.data('type'))).style('display', 'none')
      if (highlight?.length) {
        const h = new Set(highlight); c.elements().addClass('dim')
        c.nodes().filter(n => h.has(n.id())).removeClass('dim').addClass('hl')
        c.edges().filter(e => h.has(e.source().id()) && h.has(e.target().id())).removeClass('dim').addClass('hl')
      }
    })
  }, [highlight, hiddenLabels, hiddenRels, graph])
  useEffect(() => { const c = cy.current; if (!c) return; c.elements().unselect(); if (selectedId) c.getElementById(selectedId).select() }, [selectedId, graph])
  const fit = () => cy.current?.fit(undefined, 30)
  const relayout = () => cy.current?.layout({ name: 'cose', animate: false, fit: true, padding: 30, nodeRepulsion: () => 12000, idealEdgeLength: () => 95 } as any).run()
  const zoom = (f: number) => cy.current?.zoom({ level: cy.current.zoom() * f, renderedPosition: { x: (el.current?.clientWidth ?? 0) / 2, y: (el.current?.clientHeight ?? 0) / 2 } })
  const present = [...new Set(graph?.nodes.map(n => n.label))]
  return (
    <div className="relative card overflow-hidden grid-bg" style={{ height }}>
      <div ref={el} className="absolute inset-0" role="img" aria-label="Interactive graph of supply chain entities" />
      <div className="absolute top-2 right-2 flex gap-1">
        {([[Maximize2, 'Fit to screen', fit], [ZoomIn, 'Zoom in', () => zoom(1.3)], [ZoomOut, 'Zoom out', () => zoom(0.77)], [RotateCcw, 'Reset layout', relayout]] as const).map(([I, l, f]) =>
          <button key={l} onClick={f} title={l} aria-label={l} className="p-1.5 rounded bg-panel border border-line hover:border-accent"><I size={14} /></button>)}
      </div>
      <div className="absolute bottom-2 left-2 flex flex-wrap gap-x-3 gap-y-1 bg-panel/90 border border-line rounded px-2 py-1 max-w-[80%]" aria-label="Legend">
        {present.map(l => <span key={l} className="flex items-center gap-1 font-mono text-[10px] text-mute"><i className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: COLORS[l] }} />{l}</span>)}
      </div>
      {graph?.truncated && <div className="absolute top-2 left-2 chip bg-panel">truncated to node limit</div>}
      {tip && <div className="absolute pointer-events-none z-10 bg-panel border border-accent rounded px-2 py-1 text-xs shadow-lg max-w-[240px]" style={{ left: tip.x + 14, top: tip.y + 8 }}>
        <div className="font-mono text-accent">{tip.n.label}</div><div className="font-semibold">{tip.n.name}</div>
        {tip.n.properties.role && <div className="text-mute">{tip.n.properties.role} · {tip.n.properties.verificationStatus}</div>}</div>}
    </div>)
}

export function State({ loading, error, empty, children }: { loading?: boolean; error?: { message: string; status: number }; empty?: string | false; children: ReactNode }) {
  if (loading) return <div className="card p-8 flex items-center gap-3 text-mute" role="status"><Loader2 className="animate-spin" size={18} />Loading from Neo4j…</div>
  if (error) return <div className="card p-6 border-coral" role="alert"><div className="flex items-center gap-2 text-coral font-semibold"><AlertTriangle size={18} />
    {error.status === 0 || error.status === 503 ? 'Database / backend unavailable' : 'Request failed'}</div><p className="mt-2 text-sm text-mute">{error.message}</p>
    {(error.status === 0 || error.status === 503) && <p className="mt-2 text-xs text-mute font-mono">Start Neo4j Desktop and the API (see docs/LOCAL_SETUP.md), then reload.</p>}</div>
  if (empty) return <div className="card p-8 text-center text-mute">{empty}</div>
  return <>{children}</>
}

export function PropTable({ props }: { props: Record<string, any> }) {
  return <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">{Object.entries(props).map(([k, v]) => <Fragment key={k}><dt className="font-mono text-mute">{k}</dt><dd className="font-mono break-all">{String(v ?? '—')}</dd></Fragment>)}</dl>
}

const FILE: Record<string, string> = { Tablet: 'blister', Capsule: 'capsule', Bottle: 'bottle', Vial: 'vial', Box: 'carton' }
export function ProductImage({ form, name, className = '' }: { form?: string; name: string; className?: string }) {
  return <img src={`/products/${FILE[form ?? ''] ?? 'carton'}.svg`} alt={`Illustrative ${form ?? 'package'} for ${name} (fictional product)`}
    className={`w-full aspect-[4/3] object-cover rounded-md bg-[#18283A] ${className}`} loading="lazy" />
}
export const Stat = ({ label, value }: { label: string; value?: number | string }) =>
  <div className="card p-4"><div className="font-head text-2xl text-accent">{value ?? '—'}</div><div className="font-mono text-[11px] tracking-widest text-mute mt-1">{label.toUpperCase()}</div></div>

export function DataTable({ rows, max = 200 }: { rows: Record<string, any>[]; max?: number }) {
  if (!rows.length) return <div className="text-xs text-mute p-3">Query returned no rows.</div>
  const cols = Object.keys(rows[0]); const fmt = (v: any) => v && typeof v === 'object' ? (v.label && v.properties ? `${v.label}:${v.name}` : JSON.stringify(v)) : String(v ?? '—')
  return <div className="overflow-auto max-h-80"><table className="w-full text-xs font-mono"><thead className="text-mute text-left sticky top-0 bg-card"><tr>{cols.map(c => <th key={c} className="pr-3 py-1">{c}</th>)}</tr></thead>
    <tbody>{rows.slice(0, max).map((r, i) => <tr key={i} className="border-t border-line">{cols.map(c => <td key={c} className="pr-3 py-1 align-top break-all">{fmt(r[c])}</td>)}</tr>)}</tbody></table></div>
}
export function PlanTree({ plan, depth = 0 }: { plan: any; depth?: number }) {
  if (!plan) return null
  return <div style={{ marginLeft: depth * 14 }} className="font-mono text-xs border-l border-line pl-2 my-1">
    <span className="text-accent">{plan.operator}</span> <span className="text-mute">{plan.rows != null && `rows ${plan.rows} · `}{plan.dbHits != null && `dbHits ${plan.dbHits} · `}{plan.estimatedRows != null && `est ${plan.estimatedRows}`}</span>
    {plan.children?.map((c: any, i: number) => <PlanTree key={i} plan={c} depth={depth + 1} />)}</div>
}
export function downloadText(name: string, text: string) {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/markdown' })); a.download = name; a.click(); URL.revokeObjectURL(a.href)
}
export const SynthNote = () => <p className="text-[11px] font-mono text-mute">SYNTHETIC DATA · findings are rule-based indicators, not proof of fraud or misconduct.</p>
