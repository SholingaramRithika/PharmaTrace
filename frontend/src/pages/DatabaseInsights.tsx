import { useEffect, useMemo } from 'react'
import { useApi, Graph } from '../api'
import { DataTable, GraphView, PlanTree, State, Stat } from '../components'

export default function DatabaseInsights() {
  useEffect(() => { document.title = 'Database Insights · PharmaTrace' }, [])
  const r = useApi<any>('/api/insights'); const d = r.data
  const schema = useMemo<Graph | undefined>(() => d && ({ nodes: [...new Set<string>(d.schemaTriples.flatMap((t: any) => [t.source, t.target]))].map(l => ({ id: `${l}:schema`, label: l, name: l, properties: { nodesWithLabel: d.nodesByLabel.find((x: any) => x.label === l)?.count } })),
    edges: d.schemaTriples.map((t: any, i: number) => ({ id: `s${i}`, source: `${t.source}:schema`, target: `${t.target}:schema`, type: `${t.type} ×${t.count}`, properties: { count: t.count } })) }), [d])
  return <div className="max-w-[1500px] mx-auto px-4 py-6"><p className="eyebrow">DATABASE INSIGHTS</p><h1 className="font-head text-3xl mt-1">Database Insights</h1>
    <State loading={r.loading} error={r.error}>{d && <div className="space-y-4 mt-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3"><Stat label="Total nodes" value={d.totalNodes} /><Stat label="Total relationships" value={d.totalRelationships} /><Stat label="Indexes" value={d.indexes.length} /><Stat label="Constraints" value={d.constraints.length} /></div>
      <div className="grid xl:grid-cols-[minmax(0,1fr)_380px] gap-3"><div><h2 className="font-head text-sm text-mute mb-1">GRAPH SCHEMA (derived from the live data; edge label = type × count)</h2><GraphView graph={schema} height={480} /></div>
        <div className="space-y-3"><div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">NODES BY LABEL</h2><DataTable rows={d.nodesByLabel} /></div><div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">RELATIONSHIPS BY TYPE</h2><DataTable rows={d.relationshipsByType} /></div></div></div>
      <div className="grid lg:grid-cols-2 gap-3"><div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">MOST CONNECTED ENTITIES (degree)</h2>{d.degreeStats && <p className="text-xs font-mono text-mute mb-1">degree min {d.degreeStats.min} · avg {d.degreeStats.avg} · max {d.degreeStats.max} over {d.degreeStats.nodes} nodes</p>}<DataTable rows={d.topDegree} /></div>
        <div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">CONSTRAINTS</h2><DataTable rows={d.constraints} /></div></div>
      <div className="card p-3"><h2 className="font-head text-sm text-mute mb-1">INDEXES</h2><DataTable rows={d.indexes} /></div>
      <div><h2 className="font-head text-sm text-mute mb-2">QUERY PROFILING (PROFILE, measured live)</h2><div className="grid lg:grid-cols-3 gap-3">{d.profiles.map((p: any) => <div key={p.title} className="card p-3"><div className="font-semibold text-sm">{p.title}</div>
        <pre className="text-[11px] font-mono text-mute whitespace-pre-wrap my-1">{p.cypher.replace('PROFILE ', '')}</pre><div className="text-xs font-mono mb-1">total dbHits {p.totalDbHits} · available {p.timing.resultAvailableAfterMs} ms</div><PlanTree plan={p.plan} /></div>)}</div>
        <p className="text-[11px] text-mute mt-2">{d.note}</p></div>
      <div className="card p-4 text-sm text-mute"><h2 className="font-head text-sm text-accent mb-1">HOW THE GRAPH MODEL SUPPORTS TRACEABILITY</h2>A batch is a node connected to its medicine, manufacturer, suppliers, shipment legs, warehouses and pharmacies. Upstream tracing, downstream tracing and recall impact are path patterns over those stored relationships, so the number of hops is part of the query rather than a series of joins. The constraints above keep identifiers unique; the indexes make the starting-node lookup cheap.</div></div>}</State></div>
}
