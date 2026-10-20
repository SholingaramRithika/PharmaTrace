import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, useApi, Graph, GNode } from '../api'
import { GraphView, PropTable, ProductImage, State } from '../components'

const Sel = ({ v, set, opts, label }: { v: string; set: (s: string) => void; opts: [string, string][]; label: string }) =>
  <label className="text-[11px] font-mono text-mute flex flex-col gap-1">{label}<select value={v} onChange={e => set(e.target.value)} className="bg-panel border border-line rounded px-2 py-1.5 text-sm text-ink font-body">{opts.map(([k, t]) => <option key={k} value={k}>{t}</option>)}</select></label>

export default function Medicines() {
  const [sp, setSp] = useSearchParams(); const open = sp.get('open')
  const [q, setQ] = useState(''); const [cat, setCat] = useState(''); const [mf, setMf] = useState(''); const [bs, setBs] = useState(''); const [ex, setEx] = useState(''); const [rc, setRc] = useState(''); const [sort, setSort] = useState('name')
  const all = useApi<any>('/api/medicines'); const qs = new URLSearchParams({ sort, ...(q && { q }), ...(cat && { category: cat }), ...(mf && { manufacturer: mf }), ...(bs && { batchStatus: bs }), ...(ex && { expiry: ex }), ...(rc && { recall: rc }) })
  const list = useApi<any>(`/api/medicines?${qs}`)
  const cats = useMemo<string[]>(() => [...new Set<string>(all.data?.medicines.map((m: any) => m.category))].sort(), [all.data]); const mfs = useMemo<string[]>(() => [...new Set<string>(all.data?.medicines.flatMap((m: any) => m.manufacturers))].sort(), [all.data])
  const med = all.data?.medicines.find((m: any) => m.medicineId === open)
  const [graph, setGraph] = useState<Graph | undefined>(); const [gerr, setGerr] = useState(''); const [node, setNode] = useState<GNode | null>(null)
  useEffect(() => { setGraph(undefined); setGerr(''); setNode(null); if (open) api<Graph>(`/api/medicines/${open}/graph`).then(setGraph).catch(e => setGerr(e.message)) }, [open])
  const expand = (n: GNode) => api<Graph>(`/api/graph/neighbors/${encodeURIComponent(n.id)}?limit=25`).then(r => setGraph(g => g && ({ nodes: [...new Map([...g.nodes, ...r.nodes].map(x => [x.id, x])).values()], edges: [...new Map([...g.edges, ...r.edges].map(x => [x.id, x])).values()] }))).catch(e => setGerr(e.message))

  if (open) return <div className="max-w-[1500px] mx-auto px-4 py-6">
    <button onClick={() => setSp({})} className="text-accent text-xs font-mono mb-3">← ALL MEDICINES</button>
    <State loading={all.loading} error={all.error} empty={!med && !all.loading && `Medicine ${open} not found.`}>{med && <div className="grid lg:grid-cols-[320px_minmax(0,1fr)] gap-5">
      <div className="space-y-3"><ProductImage form={med.form} name={med.name} /><p className="text-[10px] font-mono text-mute">Illustrative packaging of a fictional product.</p>
        <div className="card p-4"><h1 className="font-head text-xl">{med.name}</h1><div className="mt-3"><PropTable props={{ medicineId: med.medicineId, drugCode: med.drugCode, category: med.category, form: med.form, manufacturers: med.manufacturers.join(', '), batches: med.batchCount, expired: med.expiredBatches, expiringIn6Months: med.expiringSoonBatches, recall: med.recallStatus }} /></div></div>
        <div className="card p-4 text-xs">{node ? <><div className="font-mono text-accent">{node.label}</div><div className="font-semibold mb-2">{node.name}</div><PropTable props={node.properties} />
          {node.label === 'Batch' && <Link to={`/traceability?batch=${node.properties.batchId}`} className="block mt-2 text-coral font-mono">TRACE BATCH →</Link>}</> : <span className="text-mute">Click a graph node for properties; double-click to expand.</span>}</div></div>
      <div><h2 className="font-head text-sm text-mute mb-2">NEO4J RELATIONSHIP GRAPH</h2>{gerr ? <State error={{ message: gerr, status: 0 }}><></></State> : !graph ? <State loading><></></State> :
        <GraphView graph={graph} height={600} onNode={setNode} onExpand={expand} selectedId={node?.id} />}</div></div>}</State></div>

  return <div className="max-w-[1500px] mx-auto px-4 py-6"><p className="eyebrow">MEDICINE &amp; BATCH EXPLORER</p><h1 className="font-head text-3xl mt-1">Products</h1>
    <p className="text-xs text-mute mt-1">Fictional products. Package illustrations are illustrative only; all data and relationships come from Neo4j.</p>
    <div className="card p-3 mt-4 grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-2 items-end">
      <label className="text-[11px] font-mono text-mute flex flex-col gap-1 col-span-2">SEARCH NAME / CODE<input value={q} onChange={e => setQ(e.target.value)} className="bg-panel border border-line rounded px-2 py-1.5 text-sm text-ink font-body" placeholder="Cardiolix, CRD-050" /></label>
      <Sel label="CATEGORY" v={cat} set={setCat} opts={[['', 'All'], ...cats.map(c => [c, c] as [string, string])]} /><Sel label="MANUFACTURER" v={mf} set={setMf} opts={[['', 'All'], ...mfs.map(c => [c, c] as [string, string])]} />
      <Sel label="BATCH STATUS" v={bs} set={setBs} opts={[['', 'Any'], ['Released', 'Released'], ['Recalled', 'Recalled'], ['Expired', 'Expired'], ['Quarantined', 'Quarantined']]} />
      <Sel label="EXPIRY" v={ex} set={setEx} opts={[['', 'Any'], ['expired', 'Has expired'], ['expiring', 'Expiring ≤6 mo'], ['ok', 'OK']]} /><Sel label="RECALL" v={rc} set={setRc} opts={[['', 'Any'], ['active', 'Active recall'], ['none', 'None']]} />
      <Sel label="SORT" v={sort} set={setSort} opts={[['name', 'Name'], ['code', 'Code'], ['category', 'Category'], ['batches', 'Batches']]} /></div>
    <div className="mt-4"><State loading={list.loading} error={list.error} empty={list.data && !list.data.medicines.length && 'No medicines match the current filters.'}>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">{list.data?.medicines.map((m: any) => <article key={m.medicineId} className="card p-3 flex flex-col hover:border-accent transition-colors">
        <ProductImage form={m.form} name={m.name} /><h2 className="font-semibold mt-3">{m.name}</h2><div className="font-mono text-xs text-mute">{m.drugCode} · {m.category}</div>
        <div className="text-xs text-mute mt-1">{m.manufacturers.join(', ') || 'No manufacturer linked'}</div>
        <div className="flex flex-wrap gap-1 mt-2"><span className="chip">{m.batchCount} batches</span>{Object.entries(m.batchStatus).map(([k, v]) => <span key={k} className="chip">{k} {v as number}</span>)}
          <span className={`chip ${m.expiryStatus === 'expired' ? 'text-coral border-coral' : ''}`}>expiry: {m.expiryStatus}</span><span className={`chip ${m.recallStatus === 'active' ? 'text-coral border-coral' : ''}`}>recall: {m.recallStatus}</span></div>
        <button onClick={() => setSp({ open: m.medicineId })} className="btn-ghost mt-3">VIEW GRAPH</button></article>)}</div></State></div></div>
}
