import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, Graph, GNode, GEdge, useApi } from '../api'
import { COLORS, GraphView, PropTable } from '../components'

const RELS = ['HAS_BATCH', 'MANUFACTURES', 'SUPPLIES_TO', 'TRANSPORTED_IN', 'FOLLOWED_BY', 'SHIPPED_FROM', 'DELIVERED_TO', 'HANDLED_BY', 'STORED_AT', 'DISPENSED_AT', 'AFFECTED_BY', 'HAS_EVENT', 'RECORDED_AT', 'OPERATED_BY']
const merge = (a: Graph, b: Graph): Graph => ({ nodes: [...new Map([...a.nodes, ...b.nodes].map(n => [n.id, n])).values()], edges: [...new Map([...a.edges, ...b.edges].map(e => [e.id, e])).values()] })
const toggle = (arr: string[], x: string) => arr.includes(x) ? arr.filter(y => y !== x) : [...arr, x]

export default function GraphExplorer() {
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] })
  const [q, setQ] = useState(''); const [results, setResults] = useState<GNode[] | null>(null)
  const [hiddenL, setHL] = useState<string[]>([]); const [hiddenR, setHR] = useState<string[]>([])
  const [sel, setSel] = useState<GNode | null>(null); const [edge, setEdge] = useState<GEdge | null>(null)
  const [pathFrom, setPathFrom] = useState<GNode | null>(null); const [hl, setHl] = useState<string[]>([])
  const [msg, setMsg] = useState<string>(''); const [busy, setBusy] = useState(false)
  const detail = useApi<any>(sel ? `/api/graph/node/${encodeURIComponent(sel.id)}` : null)
  const guard = async (f: () => Promise<void>) => { setBusy(true); setMsg(''); try { await f() } catch (e: any) { setMsg(e.message) } finally { setBusy(false) } }
  const add = (g: Graph) => setGraph(p => merge(p, g))
  const search = () => q.trim() && guard(async () => { const r = await api<{ results: GNode[] }>(`/api/graph/search?q=${encodeURIComponent(q.trim())}&limit=20`); setResults(r.results); if (!r.results.length) setMsg('No entities match that search.') })
  const expand = (n: GNode) => guard(async () => { const r = await api<Graph>(`/api/graph/neighbors/${encodeURIComponent(n.id)}?limit=30`); add(r); setMsg(`Expanded ${n.name}: +${r.nodes.length} nodes (bounded to 30 relationships).`) })
  const open = (n: GNode) => { add({ nodes: [n], edges: [] }); setSel(n); setEdge(null); expand(n) }
  const findPath = (to: GNode) => pathFrom && guard(async () => { const r = await api<Graph & { hops: number }>(`/api/graph/path?fromId=${encodeURIComponent(pathFrom.id)}&toId=${encodeURIComponent(to.id)}`); add(r); setHl(r.nodes.map(n => n.id)); setMsg(`Shortest path: ${r.hops} hops.`); setPathFrom(null) })
  useEffect(() => { document.title = 'Graph Explorer · PharmaTrace' }, [])
  const labels = useMemo(() => [...new Set(graph.nodes.map(n => n.label))], [graph])
  return <div className="max-w-[1700px] mx-auto px-4 py-4 grid lg:grid-cols-[260px_minmax(0,1fr)_300px] gap-3">
    <aside className="card p-3 space-y-4 self-start">
      <h1 className="font-head text-lg">Graph Explorer</h1>
      <form onSubmit={e => { e.preventDefault(); search() }}><label className="font-mono text-[11px] text-mute" htmlFor="gq">SEARCH NAME OR ID</label>
        <div className="flex gap-1 mt-1"><input id="gq" value={q} onChange={e => setQ(e.target.value)} placeholder="BATCH-001, Cardiolix…" className="flex-1 min-w-0 bg-panel border border-line rounded px-2 py-1.5 text-sm font-mono" /><button className="btn-ghost !px-3 !py-1.5" disabled={busy}>GO</button></div></form>
      {results && <ul className="max-h-48 overflow-auto text-xs space-y-1">{results.map(n => <li key={n.id}><button onClick={() => open(n)} className="w-full text-left px-2 py-1 rounded hover:bg-panel flex gap-2"><i className="w-2 h-2 mt-1 rounded-sm shrink-0" style={{ background: COLORS[n.label] }} /><span><b>{n.name}</b> <span className="text-mute font-mono">{n.label}</span></span></button></li>)}</ul>}
      <div><div className="font-mono text-[11px] text-mute mb-1">NODE TYPES (shown)</div><div className="flex flex-wrap gap-1">{labels.length ? labels.map(l => <button key={l} aria-pressed={!hiddenL.includes(l)} onClick={() => setHL(toggle(hiddenL, l))} className={`chip ${hiddenL.includes(l) ? 'opacity-40 line-through' : 'chip-on'}`}>{l}</button>) : <span className="text-xs text-mute">search to begin</span>}</div></div>
      <div><div className="font-mono text-[11px] text-mute mb-1">RELATIONSHIPS (shown)</div><div className="flex flex-wrap gap-1">{RELS.filter(r => graph.edges.some(e => e.type === r)).map(r => <button key={r} aria-pressed={!hiddenR.includes(r)} onClick={() => setHR(toggle(hiddenR, r))} className={`chip ${hiddenR.includes(r) ? 'opacity-40 line-through' : 'chip-on'}`}>{r}</button>)}</div></div>
      <button className="btn-ghost w-full" onClick={() => { setGraph({ nodes: [], edges: [] }); setSel(null); setEdge(null); setHl([]); setResults(null); setPathFrom(null); setMsg('') }}>CLEAR GRAPH</button>
      <p className="text-[11px] text-mute">Click: inspect · double-click: expand (bounded) · filters only hide, they never alter data.</p>
    </aside>
    <section className="min-w-0">
      {msg && <div className="card px-3 py-2 mb-2 text-xs" role="status">{msg}</div>}
      {pathFrom && <div className="card px-3 py-2 mb-2 text-xs border-coral">Path start: <b>{pathFrom.name}</b>. Select the destination node, then press "Path to here".</div>}
      {!graph.nodes.length ? <div className="card p-16 text-center text-mute" style={{ minHeight: 560 }}>Empty canvas. Search for a batch, medicine, organization or pharmacy to load it with its neighbours.</div>
        : <GraphView graph={graph} height={620} highlight={hl.length ? hl : undefined} hiddenLabels={hiddenL} hiddenRels={hiddenR} selectedId={sel?.id}
          onNode={n => { setSel(n); setEdge(null) }} onEdge={e => { setEdge(e); setSel(null) }} onExpand={expand} />}
    </section>
    <aside className="card p-3 self-start text-sm">
      {sel ? <><div className="font-mono text-[11px] text-accent">{sel.label}</div><h2 className="font-semibold mb-2">{sel.name}</h2><PropTable props={sel.properties} />
        {detail.data && <div className="mt-3 text-xs"><div className="font-mono text-mute">DEGREE {detail.data.degree}</div><ul className="font-mono text-mute">{detail.data.connections.map((c: any, i: number) => <li key={i}>{c.outgoing ? '→' : '←'} {c.type} ×{c.count}</li>)}</ul></div>}
        <div className="flex flex-wrap gap-1 mt-3"><button className="btn-ghost !px-3 !py-1.5" onClick={() => expand(sel)} disabled={busy}>EXPAND</button>
          <button className="btn-ghost !px-3 !py-1.5" onClick={() => { setPathFrom(sel); setHl([]) }}>PATH FROM</button>
          {pathFrom && pathFrom.id !== sel.id && <button className="btn-primary !px-3 !py-1.5" onClick={() => findPath(sel)}>PATH TO HERE</button>}
          {hl.length > 0 && <button className="btn-ghost !px-3 !py-1.5" onClick={() => setHl([])}>CLEAR PATH</button>}</div>
        {sel.label === 'Batch' && <Link className="block mt-3 text-coral font-mono text-xs" to={`/traceability?batch=${sel.properties.batchId}`}>OPEN TRACEABILITY →</Link>}</>
        : edge ? <><div className="font-mono text-[11px] text-accent">RELATIONSHIP</div><h2 className="font-semibold">{edge.type}</h2><p className="text-xs text-mute my-2">{graph.nodes.find(n => n.id === edge.source)?.name} → {graph.nodes.find(n => n.id === edge.target)?.name}</p><PropTable props={Object.keys(edge.properties).length ? edge.properties : { properties: 'none' }} /></>
        : <p className="text-mute text-xs">Select a node or relationship to inspect its properties.</p>}
    </aside></div>
}
