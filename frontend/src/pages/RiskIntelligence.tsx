import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, useApi } from '../api'
import { GraphView, PropTable, State, SynthNote } from '../components'

const SEV = ['', 'High', 'Medium', 'Low']
export default function RiskIntelligence() {
  const [sev, setSev] = useState(''); const [q, setQ] = useState(''); const [sel, setSel] = useState<string | null>(null)
  useEffect(() => { document.title = 'Risk Intelligence · PharmaTrace' }, [])
  const list = useApi<any>(`/api/risk/findings?${new URLSearchParams({ ...(sev && { severity: sev }), ...(q && { q }) })}`)
  const det = useApi<any>(sel ? `/api/risk/findings/${encodeURIComponent(sel)}` : null)
  const f = det.data?.finding
  return <div className="max-w-[1600px] mx-auto px-4 py-6"><p className="eyebrow">RISK INTELLIGENCE</p><h1 className="font-head text-3xl mt-1">Risk Intelligence</h1><div className="mt-1"><SynthNote /></div>
    <div className="card p-3 mt-4 flex flex-wrap gap-3 items-end">
      <div className="flex gap-1" role="group" aria-label="Severity filter">{SEV.map(s => <button key={s || 'all'} aria-pressed={sev === s} onClick={() => setSev(s)} className={`chip ${sev === s ? 'chip-on' : ''}`}>{s || 'All'}</button>)}</div>
      <label className="text-[11px] font-mono text-mute">SEARCH<input value={q} onChange={e => setQ(e.target.value)} placeholder="batch, rule, text" className="ml-2 bg-panel border border-line rounded px-2 py-1 text-sm text-ink font-body" /></label>
      {list.data && <div className="ml-auto flex gap-2 flex-wrap text-xs font-mono"><span className="chip">{list.data.count} shown</span><span className="chip">{list.data.summary.total} total</span>{Object.entries(list.data.summary.bySeverity).map(([k, v]) => <span key={k} className="chip">{k} {v as number}</span>)}</div>}</div>
    <div className="grid xl:grid-cols-[380px_minmax(0,1fr)] gap-3 mt-3">
      <div><State loading={list.loading} error={list.error} empty={list.data && !list.data.findings.length && 'No findings match the current filters.'}>
        <ul className="space-y-2 max-h-[720px] overflow-auto">{list.data?.findings.map((x: any) => <li key={x.findingId}><button onClick={() => setSel(x.findingId)} aria-pressed={sel === x.findingId}
          className={`card p-3 w-full text-left hover:border-accent ${sel === x.findingId ? 'border-accent' : ''}`}><div className="flex justify-between"><span className="font-mono text-[11px] text-accent">{x.rule}</span>
          <span className={`chip ${x.severity === 'High' ? 'text-coral border-coral' : ''}`}>{x.severity}</span></div><div className="font-semibold text-sm mt-1">{x.ruleTitle}</div><div className="font-mono text-xs text-mute">{x.batchId} · batch score {x.batchRiskScore} ({x.batchRiskBand})</div></button></li>)}</ul>
        {list.data && <details className="card p-3 mt-2 text-xs text-mute"><summary className="cursor-pointer">Scoring formula</summary>riskScore(batch) = Σ severity weights (High {list.data.scoring.weights.High}, Medium {list.data.scoring.weights.Medium}, Low {list.data.scoring.weights.Low}). Bands: none 0 · low 1–2 · elevated 3–4 · high ≥5. {list.data.disclaimer}</details>}</State></div>
      <div>{!sel ? <div className="card p-16 text-center text-mute">Select a finding to see its evidence graph and recommended steps.</div> :
        <State loading={det.loading} error={det.error}>{f && <div className="space-y-3">
          <div className="card p-4"><div className="font-mono text-[11px] text-accent">{f.findingId}</div><h2 className="font-head text-lg">{f.ruleTitle}</h2>
            <p className="text-sm mt-2">{f.explanation}</p><div className="grid md:grid-cols-2 gap-4 mt-3"><div><div className="font-mono text-[11px] text-mute mb-1">EVIDENCE</div><PropTable props={f.evidence} /></div>
              <div className="text-xs"><div className="font-mono text-[11px] text-mute mb-1">RULE · SEVERITY · ENTITY</div>{f.rule} · {f.severity} · <Link className="text-accent" to={`/traceability?batch=${f.batchId}`}>{f.batchId}</Link>
                <div className="font-mono text-[11px] text-mute mt-3 mb-1">RECOMMENDED NEXT ACTION</div>{f.recommendedAction}</div></div><div className="mt-2"><SynthNote /></div></div>
          <GraphView graph={det.data.graph} highlight={det.data.highlight} height={480} /></div>}</State>}</div></div></div>
}
