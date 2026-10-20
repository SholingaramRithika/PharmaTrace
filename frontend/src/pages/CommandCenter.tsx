import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useApi, Graph } from '../api'
import { GraphView, State, Stat } from '../components'

const STATUS_COLOR: Record<string, string> = { Released: '#7CCB92', Recalled: '#E5484D', Expired: '#E8B84A', Quarantined: '#80B8CC' }
export default function CommandCenter() {
  const ov = useApi<any>('/api/overview'); const g = useApi<Graph>('/api/graph/demo?batchId=BATCH-RECALL-001')
  const d = ov.data, c = d?.counts, rs = d?.riskSummary
  return <div className="max-w-[1500px] mx-auto px-4 py-6">
    <p className="eyebrow">COMMAND CENTER</p><h1 className="font-head text-3xl mt-1 mb-5">Supply chain at a glance</h1>
    <State loading={ov.loading} error={ov.error}>
      {d && <>
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-3">{c && Object.entries({ Medicines: c.medicines, Batches: c.batches, Orgs: c.organizations, Shipments: c.shipments, Pharmacies: c.pharmacies, Events: c.events, Relationships: c.relationships, Recalls: c.recalls }).map(([k, v]) => <Stat key={k} label={k} value={v as number} />)}</div>
      <div className="grid xl:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] gap-4 mt-4">
        <div><h2 className="font-head text-sm mb-2 text-mute">RECALL SCENARIO GRAPH · BATCH-RECALL-001</h2>
          <State loading={g.loading} error={g.error}><GraphView graph={g.data} height={520} /></State></div>
        <div className="space-y-4">
          <div className="card p-4"><h2 className="font-head text-sm text-mute mb-2">BATCH STATUS</h2>
            <div style={{ height: 180 }}><ResponsiveContainer><BarChart data={d.batchStatus}><CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--line))" /><XAxis dataKey="status" tick={{ fill: 'rgb(var(--mute))', fontSize: 11 }} /><YAxis allowDecimals={false} tick={{ fill: 'rgb(var(--mute))', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: 'rgb(var(--panel))', border: '1px solid rgb(var(--line))', color: 'rgb(var(--ink))' }} /><Bar dataKey="count">{d.batchStatus.map((s: any) => <Cell key={s.status} fill={STATUS_COLOR[s.status] ?? '#80B8CC'} />)}</Bar></BarChart></ResponsiveContainer></div></div>
          <div className="card p-4"><h2 className="font-head text-sm text-mute mb-2">RISK SUMMARY <span className="font-mono text-[10px]">(simulated indicators)</span></h2>
            <div className="flex gap-2 flex-wrap"><span className="chip">total {rs.total}</span>{Object.entries(rs.bySeverity).map(([k, v]) => <span key={k} className={`chip ${k === 'High' ? 'text-coral border-coral' : ''}`}>{k} {v as number}</span>)}</div>
            <ul className="mt-2 text-xs font-mono text-mute">{Object.entries(rs.byRule).map(([k, v]) => <li key={k}>{k}: {v as number}</li>)}</ul><Link to="/risk-intelligence" className="text-accent text-xs font-mono">INVESTIGATE →</Link></div>
          <div className="card p-4"><h2 className="font-head text-sm text-mute mb-2">RECALLS</h2>{d.recalls.map((r: any) => <div key={r.recallId} className="text-xs mb-2"><span className="font-mono text-accent">{r.recallId}</span> <span className={`chip ${r.status === 'Active' ? 'text-coral border-coral' : ''}`}>{r.status}</span> · {r.batches} batches<div className="text-mute">{r.reason}</div></div>)}
            <Link to="/recall-analysis" className="text-accent text-xs font-mono">IMPACT ANALYSIS →</Link></div></div></div>
      <div className="card p-4 mt-4"><h2 className="font-head text-sm text-mute mb-2">RECENT STORED TRACEABILITY EVENTS</h2>
        <table className="w-full text-xs font-mono"><thead className="text-mute text-left"><tr><th>TIME</th><th>EVENT</th><th>BATCH</th><th>DESCRIPTION</th></tr></thead><tbody>{d.recentEvents.map((e: any) => <tr key={e.eventId} className="border-t border-line"><td className="py-1">{e.timestamp}</td><td>{e.eventType}</td><td><Link className="text-accent" to={`/traceability?batch=${e.batchId}`}>{e.batchId}</Link></td><td className="text-mute">{e.description}</td></tr>)}</tbody></table></div>
      </>}
    </State></div>
}
