import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, useApi, Graph, GNode } from '../api'
import { GraphView, State, Stat, ProductImage } from '../components'

const MODULES = [['/command-center', 'Command Center', 'Live counts, status mix, events'], ['/graph-explorer', 'Graph Explorer', 'Search, filter, expand, find paths'],
  ['/medicines', 'Medicines', 'Products and their supply graphs'], ['/traceability', 'Traceability', 'Upstream & downstream by batch'],
  ['/risk-intelligence', 'Risk Intelligence', 'Explainable rule findings'], ['/recall-analysis', 'Recall Analysis', 'Impact via graph traversal'],
  ['/database-lab', 'Database Lab', 'Allowlisted Cypher, plans, CRUD'], ['/database-insights', 'Insights', 'Schema, indexes, profiling']]

export default function Home() {
  const nav = useNavigate()
  const g = useApi<Graph & { batchId: string }>('/api/graph/demo?batchId=BATCH-RECALL-001')
  const ov = useApi<any>('/api/overview'); const meds = useApi<any>('/api/medicines?sort=batches')
  const [sel, setSel] = useState<GNode | null>(null)
  const [demo, setDemo] = useState<{ loading?: boolean; data?: any; error?: string }>({})
  const runDemo = async () => { setDemo({ loading: true }); try { setDemo({ data: await api('/api/traceability/BATCH-VALID-001') }) } catch (e: any) { setDemo({ error: e.message }) } }
  const c = ov.data?.counts
  return <div>
    <section className="max-w-[1500px] mx-auto px-4 pt-10 pb-6 grid lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] gap-8 items-center">
      <div>
        <p className="eyebrow flex items-center gap-3"><span className="w-10 h-px bg-accent" />NEXT-GEN PHARMACEUTICAL INTELLIGENCE</p>
        <h1 className="font-head font-black leading-[1.02] mt-5 text-5xl xl:text-7xl"><span className="block">TRACE EVERY</span><span className="block text-accent">BATCH.</span><span className="block text-coral text-4xl xl:text-5xl tracking-wide mt-1">TRUST THE CHAIN.</span></h1>
        <p className="text-mute mt-6 max-w-xl">An interactive graph intelligence platform for pharmaceutical batch traceability, supply chain risk investigation and recall impact analysis.</p>
        <div className="flex flex-wrap gap-3 mt-7">
          <Link to="/graph-explorer" className="btn-primary">EXPLORE THE GRAPH →</Link>
          <button onClick={runDemo} className="btn-ghost" disabled={demo.loading}>{demo.loading ? 'RUNNING…' : 'RUN A TRACEABILITY DEMO ▶'}</button></div>
        {(demo.data || demo.error) && <div className="card p-4 mt-5 text-sm" role="status">
          {demo.error ? <span className="text-coral">{demo.error}</span> : <>
            <div className="font-mono text-accent text-xs mb-1">LIVE QUERY RESULT · BATCH-VALID-001</div>
            <div><b>{demo.data.medicine?.properties.name}</b> by {demo.data.manufacturers.map((m: any) => m.properties.name).join(', ')}</div>
            <div className="text-mute">{demo.data.suppliers.length} supplier · {demo.data.shipments.length} shipments · {demo.data.events.length} events · {demo.data.issues.length} findings · {demo.data.gaps.length} gaps</div>
            <Link to="/traceability" className="text-accent text-xs font-mono">OPEN TRACEABILITY →</Link></>}</div>}
        <div className="grid grid-cols-3 gap-3 mt-7 max-w-xl">
          <Stat label="Medicines" value={c?.medicines} /><Stat label="Batches" value={c?.batches} /><Stat label="Organizations" value={c?.organizations} />
          <Stat label="Shipments" value={c?.shipments} /><Stat label="Relationships" value={c?.relationships} /><Stat label="Recalls" value={c?.recalls} /></div>
        {ov.error && <p className="text-xs text-coral mt-2">Statistics unavailable: {ov.error.message}</p>}
      </div>
      <div>
        <State loading={g.loading} error={g.error} empty={g.data && !g.data.nodes.length && 'No graph data. Load the dataset first.'}>
          <GraphView graph={g.data} height={520} onNode={setSel} onExpand={n => n.label === 'Batch' && nav(`/traceability?batch=${n.properties.batchId}`)} /></State>
        <div className="card p-3 mt-2 text-xs min-h-[3rem]" aria-live="polite">{sel ? <><b className="font-mono text-accent">{sel.label}</b> {sel.name}
          {sel.label === 'Batch' && <Link className="ml-3 text-coral font-mono" to={`/traceability?batch=${sel.properties.batchId}`}>TRACE →</Link>}
          {sel.label === 'Medicine' && <Link className="ml-3 text-coral font-mono" to={`/medicines?open=${sel.properties.medicineId}`}>VIEW MEDICINE →</Link>}</>
          : <span className="text-mute">Seeded recall scenario (RCL-001) from Neo4j. Click a node to inspect · double-click a batch to trace · scroll to zoom · drag to pan.</span>}</div>
      </div>
    </section>
    <section className="max-w-[1500px] mx-auto px-4 py-8"><h2 className="font-head text-xl mb-4">GRAPH MODULES</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">{MODULES.map(([to, t, d]) => <Link key={to} to={to} className="card p-4 hover:border-accent transition-colors"><div className="font-head text-sm text-accent">{t.toUpperCase()}</div><div className="text-xs text-mute mt-1">{d}</div></Link>)}</div></section>
    <section className="max-w-[1500px] mx-auto px-4 py-8"><div className="flex items-end justify-between mb-4"><h2 className="font-head text-xl">FEATURED PRODUCTS</h2><Link to="/medicines" className="text-accent text-xs font-mono">ALL MEDICINES →</Link></div>
      <State loading={meds.loading} error={meds.error}><div className="grid sm:grid-cols-3 gap-4">{meds.data?.medicines.slice(0, 3).map((m: any) =>
        <Link key={m.medicineId} to={`/medicines?open=${m.medicineId}`} className="card p-3 hover:border-accent"><ProductImage form={m.form} name={m.name} />
          <div className="mt-2 font-semibold">{m.name}</div><div className="font-mono text-xs text-mute">{m.drugCode} · {m.category} · {m.batchCount} batches</div></Link>)}</div></State></section>
    <section className="max-w-[1500px] mx-auto px-4 py-8 grid md:grid-cols-2 gap-4">
      <div className="card p-5"><h3 className="font-head text-sm text-accent">WHY NEO4J</h3><p className="text-sm text-mute mt-2">Traceability is a question about relationships: which suppliers fed a batch, which shipments carried it, which pharmacies received it. A property graph stores those relationships as first-class records, so multi-hop questions become path patterns instead of chains of joins.</p></div>
      <div className="card p-5"><h3 className="font-head text-sm text-accent">TRACEABILITY &amp; RECALL</h3><p className="text-sm text-mute mt-2">Trace a batch upstream to its manufacturer and suppliers, or downstream to every warehouse and pharmacy. A recall is a traversal from the recall node to all affected destinations. All data shown is synthetic.</p></div></section>
  </div>
}
