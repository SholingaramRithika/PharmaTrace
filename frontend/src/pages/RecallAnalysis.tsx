import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useApi } from '../api'
import { DataTable, GraphView, State, Stat, SynthNote, downloadText } from '../components'

export default function RecallAnalysis() {
  const [q, setQ] = useState(''); const [sel, setSel] = useState<string | null>(null); const [msg, setMsg] = useState('')
  useEffect(() => { document.title = 'Recall Impact Analysis · PharmaTrace' }, [])
  const list = useApi<any>('/api/recall'); const recalls: any[] = (list.data?.recalls ?? []).filter((r: any) => !q || (r.recallId + r.reason).toLowerCase().includes(q.toLowerCase()))
  const id = sel ?? list.data?.recalls[0]?.recallId ?? null; const imp = useApi<any>(id ? `/api/recall/${id}/impact` : null); const d = imp.data
  const exportReport = async () => { try { const r = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api/recall/${id}/report`); downloadText(`recall_${id}.md`, await r.text()) } catch { setMsg('Export failed: backend unreachable') } }
  return <div className="max-w-[1600px] mx-auto px-4 py-6"><p className="eyebrow">RECALL IMPACT ANALYSIS</p><h1 className="font-head text-3xl mt-1">Recall Impact Analysis</h1><div className="mt-1"><SynthNote /></div>
    <div className="grid xl:grid-cols-[300px_minmax(0,1fr)] gap-3 mt-4">
      <aside className="card p-3 self-start"><label className="font-mono text-[11px] text-mute" htmlFor="rq">SEARCH RECALLS</label>
        <input id="rq" value={q} onChange={e => setQ(e.target.value)} placeholder="RCL-001, contamination…" className="w-full mt-1 mb-3 bg-panel border border-line rounded px-2 py-1.5 text-sm font-mono" />
        <State loading={list.loading} error={list.error} empty={list.data && !recalls.length && 'No recall matches.'}><ul className="space-y-2">{recalls.map((r: any) => <li key={r.recallId}><button onClick={() => setSel(r.recallId)} aria-pressed={id === r.recallId}
          className={`w-full text-left card p-2 hover:border-accent ${id === r.recallId ? 'border-accent' : ''}`}><span className="font-mono text-accent text-xs">{r.recallId}</span> <span className={`chip ${r.status === 'Active' ? 'text-coral border-coral' : ''}`}>{r.status}</span>
          <div className="text-xs text-mute mt-1">{r.reason}</div><div className="text-[11px] font-mono">{r.batches} batches</div></button></li>)}</ul></State></aside>
      <section className="min-w-0"><State loading={imp.loading} error={imp.error} empty={!id && !list.loading && !list.error && 'No recall records in the database.'}>{d && <div className="space-y-3">
        <div className="card p-4"><div className="flex flex-wrap justify-between gap-2"><div><div className="font-mono text-accent text-xs">{d.recall.recallId} · {d.recall.status} · issued {d.recall.issuedAt}</div><div className="font-semibold">{d.recall.reason}</div></div>
          <button className="btn-ghost" onClick={exportReport}>EXPORT REPORT (.md)</button></div>{msg && <p className="text-xs text-coral mt-1">{msg}</p>}</div>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2"><Stat label="Batches" value={d.totals.batches} /><Stat label="Units made" value={d.totals.batchUnits} /><Stat label="Units to pharmacies" value={d.totals.unitsDeliveredToPharmacies} />
          <Stat label="Pharmacies" value={d.totals.pharmacies} /><Stat label="Warehouses" value={d.totals.warehouses} /><Stat label="Distributors" value={d.totals.distributors} /></div>
        <div><h2 className="font-head text-sm text-mute mb-1">AFFECTED PATHS (all nodes shown are reached by traversal from the recall)</h2><GraphView graph={d.graph} highlight={d.highlight} height={500} /></div>
        <div className="grid lg:grid-cols-2 gap-3">
          <div className="card p-3"><h2 className="font-head text-sm text-coral mb-2">AFFECTED PHARMACIES ({d.affectedPharmacies.length})</h2><DataTable rows={d.affectedPharmacies.map((p: any) => ({ id: p.pharmacyId, name: p.name, region: p.region, units: p.units, batches: p.batches.join(', ') }))} /></div>
          <div className="card p-3"><h2 className="font-head text-sm text-mute mb-2">UNAFFECTED PHARMACIES ({d.unaffectedPharmacies.length})</h2><DataTable rows={d.unaffectedPharmacies} /></div>
          <div className="card p-3"><h2 className="font-head text-sm text-mute mb-2">AFFECTED WAREHOUSES</h2><DataTable rows={d.affectedWarehouses.map((w: any) => ({ id: w.locationId, name: w.name, batches: w.batches.join(', ') }))} /></div>
          <div className="card p-3"><h2 className="font-head text-sm text-mute mb-2">DISTRIBUTORS INVOLVED</h2><DataTable rows={d.distributors.map((w: any) => ({ id: w.organizationId, name: w.name, batches: w.batches.join(', ') }))} /></div></div>
        <div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">AFFECTED BATCHES</h2><DataTable rows={d.affectedBatches} />
          <div className="text-xs mt-2">{d.affectedBatches.map((b: any) => <Link key={b.batchId} className="text-accent font-mono mr-3" to={`/traceability?batch=${b.batchId}`}>trace {b.batchId}</Link>)}</div></div>
        <div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">LIMITATIONS</h2><ul className="text-xs text-mute list-disc ml-4">{d.limitations.map((l: string) => <li key={l}>{l}</li>)}</ul></div></div>}</State></section></div></div>
}
