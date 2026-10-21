import { useEffect, useMemo, useState } from 'react'
import { api, ApiError, useApi } from '../api'
import { DataTable, GraphView, PlanTree, State } from '../components'

export default function DatabaseLab() {
  const cat = useApi<any>('/api/lab/queries'); const [q, setQ] = useState(''); const [sel, setSel] = useState<string>('match_batch'); const [vals, setVals] = useState<Record<string, string>>({})
  const [run, setRun] = useState<{ loading?: boolean; data?: any; error?: string }>({}); const [tab, setTab] = useState<'table' | 'graph' | 'plan'>('table')
  useEffect(() => { document.title = 'Database Lab · PharmaTrace' }, [])
  const queries: any[] = cat.data?.queries ?? []; const cur = queries.find(x => x.id === sel)
  const groups = useMemo(() => { const m = new Map<string, any[]>(); queries.filter(x => !q || (x.title + x.category + x.concept).toLowerCase().includes(q.toLowerCase())).forEach(x => m.set(x.category, [...(m.get(x.category) ?? []), x])); return [...m] }, [queries, q])
  useEffect(() => { setVals({}); setRun({}) }, [sel])
  const blocked = cur?.kind === 'write' && !cat.data?.writesEnabled
  const exec = async () => { setRun({ loading: true }); try { const params = Object.fromEntries(Object.entries(vals).filter(([, v]) => v !== ''))
    const data = await api<any>('/api/lab/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ queryId: sel, params }) })
    setRun({ data }); setTab(data.plan ? 'plan' : data.graph?.nodes.length && cur?.graph ? 'graph' : 'table') } catch (e) { setRun({ error: (e as ApiError).message }) } }
  return <div className="max-w-[1600px] mx-auto px-4 py-6"><p className="eyebrow">DATABASE LAB</p><h1 className="font-head text-3xl mt-1">Database Lab</h1>
    <p className="text-xs text-mute mt-1">Only allowlisted, parameterized templates run. Write templates affect <span className="font-mono">TEST-*</span> records only and are {cat.data?.writesEnabled ? 'ENABLED' : 'DISABLED'} on this server.</p>
    <div className="grid lg:grid-cols-[300px_minmax(0,1fr)] gap-3 mt-4"><State loading={cat.loading} error={cat.error}>
      <aside className="card p-3 self-start max-h-[760px] overflow-auto"><input aria-label="Filter queries" value={q} onChange={e => setQ(e.target.value)} placeholder="Filter: MERGE, shortest, index…" className="w-full mb-3 bg-panel border border-line rounded px-2 py-1.5 text-sm" />
        {groups.map(([g, items]) => <div key={g} className="mb-3"><div className="font-mono text-[11px] text-mute mb-1">{g.toUpperCase()}</div>{items.map(x => <button key={x.id} onClick={() => setSel(x.id)} aria-pressed={sel === x.id}
          className={`block w-full text-left text-xs px-2 py-1 rounded ${sel === x.id ? 'bg-panel text-accent' : 'hover:bg-panel'}`}>{x.kind === 'write' && <span className="text-coral">✎ </span>}{x.title}</button>)}</div>)}</aside>
      {cur && <section className="min-w-0 space-y-3"><div className="card p-4"><div className="flex flex-wrap gap-2 items-center"><h2 className="font-semibold">{cur.title}</h2><span className="chip">{cur.kind}</span><span className="chip">{cur.concept}</span></div>
        <p className="text-sm text-mute mt-1">{cur.description}</p><pre className="mt-3 p-3 rounded bg-panel border border-line font-mono text-xs overflow-auto whitespace-pre-wrap">{cur.cypher}</pre>
        <div className="grid sm:grid-cols-3 gap-2 mt-3">{Object.entries<any>(cur.params).map(([k, r]) => <label key={k} className="text-[11px] font-mono text-mute flex flex-col gap-1">{k}
          {r.enum ? <select value={vals[k] ?? r.default} onChange={e => setVals({ ...vals, [k]: e.target.value })} className="bg-panel border border-line rounded px-2 py-1.5 text-sm text-ink">{r.enum.map((o: string) => <option key={o}>{o}</option>)}</select>
            : <input value={vals[k] ?? ''} placeholder={String(r.default)} onChange={e => setVals({ ...vals, [k]: e.target.value })} className="bg-panel border border-line rounded px-2 py-1.5 text-sm text-ink" />}</label>)}</div>
        <div className="flex items-center gap-3 mt-3"><button className="btn-primary" onClick={exec} disabled={run.loading || blocked}>{run.loading ? 'RUNNING…' : 'RUN QUERY ▶'}</button>{blocked && <span className="text-xs text-coral">Writes are disabled on this server (ENABLE_WRITES=false).</span>}</div></div>
        {run.error && <div className="card p-3 border-coral text-sm text-coral" role="alert">{run.error}</div>}
        {run.data && <div className="card p-4"><div className="flex flex-wrap gap-2 items-center text-xs font-mono mb-2">
          <span className="chip">rows {run.data.rows.length}</span><span className="chip">available after {run.data.timing.resultAvailableAfterMs} ms</span><span className="chip">consumed after {run.data.timing.resultConsumedAfterMs} ms</span>
          {Object.entries(run.data.counters).map(([k, v]) => <span key={k} className="chip text-coral border-coral">{k} {v as number}</span>)}
          <span className="ml-auto flex gap-1">{(['table', 'graph', 'plan'] as const).map(t => <button key={t} aria-pressed={tab === t} onClick={() => setTab(t)} className={`chip ${tab === t ? 'chip-on' : ''}`}>{t}</button>)}</span></div>
          {tab === 'table' && <DataTable rows={run.data.rows} />}
          {tab === 'graph' && (run.data.graph.nodes.length ? <GraphView graph={run.data.graph} height={420} /> : <p className="text-xs text-mute p-3">This query returned no graph elements (return paths or nodes+relationships to see a graph).</p>)}
          {tab === 'plan' && (run.data.plan ? <><p className="text-[11px] text-mute mb-1">{run.data.profiled ? 'PROFILE (executed): actual rows and db hits' : 'EXPLAIN (not executed): estimated rows'}</p><PlanTree plan={run.data.plan} /></> : <p className="text-xs text-mute p-3">No plan: run an EXPLAIN or PROFILE template.</p>)}</div>}</section>}
    </State></div></div>
}
