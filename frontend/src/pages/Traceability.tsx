import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, ApiError, Graph, GNode } from '../api'
import { DataTable, GraphView, PropTable, State, SynthNote, downloadText } from '../components'

type Dir = 'both' | 'upstream' | 'downstream'
export default function Traceability() {
  const [sp, setSp] = useSearchParams(); const batch = sp.get('batch') ?? ''; const [input, setInput] = useState(batch); const [dir, setDir] = useState<Dir>('both')
  const [st, setSt] = useState<{ loading?: boolean; data?: any; error?: ApiError }>({}); const [sel, setSel] = useState<GNode | null>(null); const [hl, setHl] = useState<string[]>([]); const [msg, setMsg] = useState('')
  useEffect(() => { document.title = 'Batch Traceability · PharmaTrace' }, [])
  useEffect(() => { if (!batch) { setSt({}); return } setSt({ loading: true }); setSel(null); setHl([]); setMsg('')
    api<any>(`/api/traceability/${encodeURIComponent(batch)}?direction=${dir}`).then(data => setSt({ data })).catch(error => setSt({ error })) }, [batch, dir])
  const d = st.data; const g: Graph | undefined = d?.graph
  const pathTo = async (n: GNode) => { try { const r = await api<Graph>(`/api/graph/path?fromId=${encodeURIComponent('Batch:' + batch)}&toId=${encodeURIComponent(n.id)}`); setHl(r.nodes.map(x => x.id)); setMsg(`Path batch → ${n.name}: ${r.edges.length} hops`) } catch (e: any) { setMsg(e.message) } }
  const exportReport = async () => { try { const r = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/api/traceability/${encodeURIComponent(batch)}/report`); downloadText(`trace_${batch}.md`, await r.text()) } catch { setMsg('Export failed: backend unreachable') } }
  return <div className="max-w-[1500px] mx-auto px-4 py-6"><p className="eyebrow">BATCH TRACEABILITY</p><h1 className="font-head text-3xl mt-1">Batch Traceability</h1>
    <form className="flex gap-2 mt-4 max-w-2xl" onSubmit={e => { e.preventDefault(); input.trim() && setSp({ batch: input.trim() }) }}>
      <label htmlFor="b" className="sr-only">Batch identifier</label><input id="b" value={input} onChange={e => setInput(e.target.value)} placeholder="Batch ID, e.g. BATCH-VALID-001" className="flex-1 bg-panel border border-line rounded px-3 py-2 font-mono" />
      <button className="btn-primary">TRACE</button></form>
    <div className="flex flex-wrap gap-1 mt-2">{['BATCH-VALID-001', 'BATCH-RECALL-001', 'BATCH-UNVER-001', 'BATCH-INCOMPLETE-001', 'BATCH-QTY-001'].map(b => <button key={b} className="chip" onClick={() => { setInput(b); setSp({ batch: b }) }}>{b}</button>)}</div>
    <div className="mt-4"><State loading={st.loading} error={st.error?.status === 404 ? undefined : st.error} empty={!batch ? 'Enter a batch identifier to trace its supply chain.' : st.error?.status === 404 ? `No batch “${batch}” exists in the database. Check the identifier; nothing has been inferred.` : false}>
      {d && <>
        <div className="grid md:grid-cols-4 gap-3">
          <div className="card p-3 md:col-span-2"><div className="font-mono text-[11px] text-accent">{d.batch.properties.batchId}</div><div className="font-semibold">{d.medicine?.properties.name ?? 'UNKNOWN MEDICINE'}</div>
            <div className="text-xs text-mute">Manufacturer: {d.manufacturers.map((m: any) => m.properties.name).join(', ') || 'UNKNOWN'}</div></div>
          <div className="card p-3 text-xs"><PropTable props={{ manufactured: d.batch.properties.manufacturingDate, expires: d.batch.properties.expiryDate, quantity: d.batch.properties.quantity, status: d.batch.properties.status }} /></div>
          <div className="card p-3 text-xs"><div className="font-mono text-mute mb-1">SUPPLIERS</div>{d.suppliers.length ? d.suppliers.map((s: any, i: number) => <div key={i}>{s.o.properties.name} <span className={s.o.properties.verificationStatus === 'Verified' ? 'text-mute' : 'text-coral'}>({s.o.properties.verificationStatus})</span></div>) : 'none recorded'}</div></div>
        <div className="flex flex-wrap items-center gap-2 mt-3"><span className="font-mono text-[11px] text-mute">TRACE:</span>
          {(['both', 'upstream', 'downstream'] as Dir[]).map(x => <button key={x} aria-pressed={dir === x} onClick={() => setDir(x)} className={`chip ${dir === x ? 'chip-on' : ''}`}>{x}</button>)}
          <button className="btn-ghost !py-1.5 ml-auto" onClick={exportReport}>EXPORT REPORT (.md)</button></div>
        {msg && <div className="card px-3 py-2 mt-2 text-xs" role="status">{msg}</div>}
        <div className="grid lg:grid-cols-[minmax(0,1fr)_280px] gap-3 mt-2">
          <GraphView graph={g} height={560} highlight={hl.length ? hl : undefined} selectedId={sel?.id} onNode={setSel} />
          <div className="card p-3 text-xs self-start">{sel ? <><div className="font-mono text-accent">{sel.label}</div><div className="font-semibold mb-2">{sel.name}</div><PropTable props={sel.properties} />
            <div className="flex gap-1 mt-2"><button className="btn-ghost !px-3 !py-1.5" onClick={() => pathTo(sel)}>PATH FROM BATCH</button>{hl.length > 0 && <button className="btn-ghost !px-3 !py-1.5" onClick={() => setHl([])}>CLEAR</button>}</div></> : <span className="text-mute">Select a node to inspect it and highlight its path from the batch.</span>}</div></div>
        <div className="grid lg:grid-cols-2 gap-3 mt-3">
          <div className="card p-3"><h2 className="font-head text-sm text-mute mb-2">SHIPMENTS &amp; DESTINATIONS</h2><DataTable rows={d.shipments.map((s: any) => ({ shipment: s.s.properties.shipmentId, from: s.origin, to: s.destination ?? 'NO DESTINATION RECORDED', region: s.destinationRegion, carrier: s.carrier, qty: s.s.properties.quantity, previousLeg: s.previousLeg, status: s.s.properties.status }))} /></div>
          <div className="card p-3"><h2 className="font-head text-sm text-mute mb-2">EVENT HISTORY (chronological)</h2><DataTable rows={d.events.map((e: any) => ({ time: e.e.properties.timestamp, event: e.e.properties.eventType, location: e.location }))} /></div></div>
        <div className="card p-3 mt-3"><h2 className="font-head text-sm text-mute mb-2">MISSING / INCONSISTENT INFORMATION</h2>
          {!d.gaps.length && !d.issues.length ? <p className="text-xs text-mute">No gaps or rule findings for this batch.</p> : <ul className="text-xs space-y-1">{d.gaps.map((x: string) => <li key={x} className="text-coral">• {x}</li>)}{d.issues.map((i: any) => <li key={i.findingId}>• <b>[{i.severity}]</b> {i.ruleTitle}: {i.explanation}</li>)}</ul>}
          <div className="mt-2"><SynthNote /></div><p className="text-[11px] text-mute mt-1">{d.note}</p></div></>}
    </State></div></div>
}
