import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { existsSync, statSync } from 'node:fs'
import App from './App'
import { ThemeProvider } from './theme'
import { ProductImage } from './components'

const MEDS = ['Tablet', 'Capsule', 'Bottle', 'Vial', 'Box'].map((form, i) => ({ medicineId: `MED-00${i}`, name: `Med ${form}`, drugCode: `C${i}`, category: 'Cat', form,
  manufacturers: ['Acme'], batchCount: 2, batchStatus: { Released: 2 }, expiredBatches: 0, expiringSoonBatches: 0, expiryStatus: 'ok', recallStatus: 'none' }))
let health: any
function mockFetch(over: Record<string, any> = {}) {
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    const p = url.replace(/^https?:\/\/[^/]+/, '')
    const key = Object.keys(over).find(k => p.startsWith(k))
    if (key) return { ok: over[key] !== null, status: over[key] === null ? 503 : 200, statusText: 'x', json: async () => over[key] ?? { error: { code: 'DATABASE_UNAVAILABLE', message: 'Cannot reach Neo4j.' } } }
    if (p.startsWith('/api/health')) return { ok: true, status: 200, json: async () => health }
    if (p.startsWith('/api/medicines')) return { ok: true, status: 200, json: async () => ({ medicines: MEDS, count: 5 }) }
    return { ok: false, status: 503, statusText: 'x', json: async () => ({ error: { code: 'DATABASE_UNAVAILABLE', message: 'Cannot reach Neo4j.' } }) }
  }))
}
const renderAt = (path: string) => render(<ThemeProvider><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></ThemeProvider>)
beforeEach(() => { health = { status: 'ok', database: { connected: true, nodes: 485 } }; mockFetch() })

describe('routes', () => {
  const routes: [string, RegExp][] = [['/', /TRACE EVERY/], ['/command-center', /Supply chain at a glance/], ['/graph-explorer', /Graph Explorer/], ['/medicines', /Products/],
    ['/traceability', /Batch Traceability/], ['/risk-intelligence', /Risk Intelligence/], ['/recall-analysis', /Recall Impact Analysis/], ['/database-lab', /Database Lab/], ['/database-insights', /Database Insights/]]
  it.each(routes)('direct access to %s renders its own page', async (path, h) => {
    renderAt(path); expect((await screen.findAllByRole('heading', { level: 1 })).some(e => h.test(e.textContent ?? ''))).toBe(true)
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeTruthy()
  })
  it('navigation links reach every route', async () => {
    renderAt('/'); const nav = within(screen.getByRole('navigation', { name: 'Primary' }))
    expect(nav.getAllByRole('link').map(a => a.getAttribute('href'))).toEqual(['/', '/command-center', '/graph-explorer', '/medicines', '/traceability', '/risk-intelligence', '/recall-analysis', '/database-lab', '/database-insights'])
    fireEvent.click(nav.getByText('GRAPH EXPLORER')); expect((await screen.findAllByText('Graph Explorer')).length).toBeGreaterThan(0)
  })
})

describe('theme toggle', () => {
  it('defaults to dark, switches to light, persists, and toggles back', async () => {
    renderAt('/'); const btn = () => screen.getByRole('button', { name: /switch to/i })
    expect(document.documentElement.dataset.theme).toBe('dark'); expect(btn().getAttribute('aria-label')).toMatch(/light/)
    fireEvent.click(btn()); expect(document.documentElement.dataset.theme).toBe('light'); expect(localStorage.getItem('pt-theme')).toBe('light')
    fireEvent.click(within(screen.getByRole('navigation', { name: 'Primary' })).getByText('MEDICINES')); await screen.findByText('Products'); expect(document.documentElement.dataset.theme).toBe('light')
    fireEvent.click(btn()); expect(document.documentElement.dataset.theme).toBe('dark'); expect(localStorage.getItem('pt-theme')).toBe('dark')
  })
  it('restores the saved theme on a fresh load', () => {
    localStorage.setItem('pt-theme', 'light'); document.documentElement.dataset.theme = 'light'; renderAt('/medicines')
    expect(document.documentElement.dataset.theme).toBe('light'); expect(screen.getByRole('button', { name: /switch to dark/i })).toBeTruthy()
  })
  it('toggle exists on every route', async () => {
    for (const p of ['/', '/command-center', '/graph-explorer', '/medicines', '/traceability', '/risk-intelligence', '/recall-analysis', '/database-lab', '/database-insights']) {
      const { unmount } = renderAt(p); expect(screen.getByRole('button', { name: /switch to/i })).toBeTruthy(); unmount() }
  })
})

describe('database status honesty', () => {
  it('shows connected only when the health check says so', async () => { renderAt('/'); expect(await screen.findByText(/NEO4J CONNECTED · 485 NODES/)).toBeTruthy() })
  it('shows disconnected when the database is down', async () => { health = { status: 'degraded', database: { connected: false } }; renderAt('/'); expect(await screen.findByText('NEO4J DISCONNECTED')).toBeTruthy(); expect(screen.queryByText(/CONNECTED ·/)).toBeNull() })
  it('shows API offline when the backend is unreachable', async () => { vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('fail') })); renderAt('/'); expect(await screen.findByText('API OFFLINE')).toBeTruthy() })
  it('never shows fabricated statistics when the API is down', async () => {
    mockFetch({ '/api/overview': null, '/api/graph/demo': null }); renderAt('/'); await waitFor(() => expect(screen.getAllByText(/Cannot reach Neo4j|unavailable/i).length).toBeGreaterThan(0))
    expect(screen.getAllByText('—').length).toBeGreaterThanOrEqual(6)
  })
})

describe('medicine product images', () => {
  it('every medicine card renders a local product image matching its form', async () => {
    renderAt('/medicines'); await screen.findByText('Med Tablet'); const imgs = screen.getAllByRole('img').filter(i => i.getAttribute('src')?.startsWith('/products/'))
    expect(imgs.map(i => i.getAttribute('src'))).toEqual(['/products/blister.svg', '/products/capsule.svg', '/products/bottle.svg', '/products/vial.svg', '/products/carton.svg'])
    imgs.forEach(i => expect(i.getAttribute('alt')).toMatch(/Illustrative .*\(fictional product\)/)); expect(screen.getAllByText('VIEW GRAPH')).toHaveLength(5)
  })
  it('falls back to a carton for an unknown form', () => { render(<ProductImage form="Mystery" name="X" />); expect(screen.getByRole('img').getAttribute('src')).toBe('/products/carton.svg') })
  it('opens the detail view with the image beside Neo4j-derived properties', async () => {
    mockFetch({ '/api/medicines/MED-001/graph': { medicineId: 'MED-001', nodes: [], edges: [] } }); renderAt('/medicines?open=MED-001')
    expect(await screen.findByText('NEO4J RELATIONSHIP GRAPH')).toBeTruthy(); expect(screen.getAllByRole('img').some(i => i.getAttribute('src') === '/products/capsule.svg')).toBe(true); expect(screen.getByText('MED-001')).toBeTruthy()
  })
  it('all bundled product assets exist and are non-empty', () => {
    for (const f of ['blister', 'capsule', 'bottle', 'vial', 'carton']) { const p = `public/products/${f}.svg`; expect(existsSync(p)).toBe(true); expect(statSync(p).size).toBeGreaterThan(500) }
    expect(existsSync('public/logo.svg')).toBe(true)
  })
})

describe('command center with data', () => {
  it('renders backend-derived counts, status chart data and events', async () => {
    mockFetch({ '/api/overview': { counts: { medicines: 8, batches: 40, organizations: 25, shipments: 133, pharmacies: 14, events: 251, relationships: 1394, recalls: 2, nodes: 485 },
      batchStatus: [{ status: 'Released', count: 36 }], recentEvents: [{ eventId: 'E1', eventType: 'DELIVERED', timestamp: '2026-09-01T10:00:00', description: 'Delivered to PH-01', batchId: 'BATCH-001' }],
      recalls: [{ recallId: 'RCL-001', status: 'Active', reason: 'Simulated reason', batches: 2 }], riskSummary: { total: 8, bySeverity: { High: 4 }, byRule: { DUPLICATE_LOT: 2 } } },
      '/api/graph/demo': { batchId: 'B', nodes: [], edges: [] } })
    renderAt('/command-center'); expect(await screen.findByText('1394')).toBeTruthy(); expect(screen.getByText('RCL-001')).toBeTruthy(); expect(screen.getByText('DUPLICATE_LOT: 2')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'BATCH-001' }).getAttribute('href')).toBe('/traceability?batch=BATCH-001')
  })
})

const P = (o: any) => ({ properties: o, label: 'X', name: 'n', id: 'X:1' })
describe('phase 3 pages', () => {
  it('traceability: unknown batch shows a helpful empty state, nothing fabricated', async () => {
    vi.stubGlobal('fetch', vi.fn(async (u: string) => u.includes('/api/traceability/') ? { ok: false, status: 404, statusText: 'x', json: async () => ({ error: { code: 'NOT_FOUND', message: 'Batch not found' } }) } : { ok: true, status: 200, json: async () => health }))
    renderAt('/traceability?batch=BATCH-NOPE'); expect(await screen.findByText(/No batch “BATCH-NOPE” exists/)).toBeTruthy()
  })
  it('traceability: renders batch details, gaps and export control', async () => {
    mockFetch({ '/api/traceability/BATCH-X': { batch: P({ batchId: 'BATCH-X', manufacturingDate: '2026-01-01', expiryDate: '2028-01-01', quantity: 5, status: 'Released' }), medicine: P({ name: 'Cardiolix' }), manufacturers: [P({ name: 'Acme' })],
      suppliers: [{ o: P({ name: 'Sup', verificationStatus: 'Unverified' }), material: 'm' }], shipments: [{ s: P({ shipmentId: 'S1', quantity: 5, status: 'InTransit' }), origin: 'A', destination: null, carrier: 'C' }], events: [], recalls: [],
      issues: [], gaps: ['Missing event: RECEIVED'], graph: { nodes: [], edges: [] }, note: 'No relationships are inferred' } })
    renderAt('/traceability?batch=BATCH-X'); expect(await screen.findByText(/Missing event: RECEIVED/)).toBeTruthy(); expect(screen.getByText('NO DESTINATION RECORDED')).toBeTruthy(); expect(screen.getByText(/EXPORT REPORT/)).toBeTruthy()
  })
  it('risk: lists findings with severity filter and synthetic disclaimer', async () => {
    mockFetch({ '/api/risk/findings?': { findings: [{ findingId: 'RF-1', rule: 'UNVERIFIED_SUPPLIER', ruleTitle: 'Unverified supplier in batch lineage', severity: 'High', batchId: 'BATCH-UNVER-001', batchRiskScore: 3, batchRiskBand: 'elevated' }], count: 1,
      summary: { total: 8, bySeverity: { High: 4 } }, scoring: { weights: { High: 3, Medium: 2, Low: 1 } }, disclaimer: 'Synthetic indicators' } })
    renderAt('/risk-intelligence'); expect(await screen.findByText('Unverified supplier in batch lineage')).toBeTruthy(); expect(screen.getAllByText(/not proof of fraud/i).length).toBeGreaterThan(0)
    fireEvent.click(screen.getByRole('button', { name: 'High' })); await waitFor(() => expect((fetch as any).mock.calls.some((c: any[]) => String(c[0]).includes('severity=High'))).toBe(true))
  })
  it('database lab: lists templates and blocks write templates when disabled', async () => {
    const q = (id: string, kind: string) => ({ id, title: id, category: 'C', kind, concept: 'k', description: 'd', cypher: 'MATCH (n) RETURN n', params: {}, graph: false })
    mockFetch({ '/api/lab/queries': { queries: [q('match_batch', 'read'), q('delete_test_batch', 'write')], writesEnabled: false } }); renderAt('/database-lab')
    expect(await screen.findByText('delete_test_batch', { exact: false })).toBeTruthy(); fireEvent.click(screen.getByText('delete_test_batch', { exact: false }))
    await waitFor(() => expect((screen.getByRole('button', { name: /RUN QUERY/ }) as HTMLButtonElement).disabled).toBe(true)); expect(screen.getAllByText(/Writes are disabled/).length).toBeGreaterThan(0)
  })
  it('recall: shows affected and unaffected pharmacies and limitations', async () => {
    mockFetch({ '/api/recall/RCL-001/impact': { recall: { recallId: 'RCL-001', status: 'Active', reason: 'Sim', issuedAt: 'x' }, affectedBatches: [{ batchId: 'B1', quantity: 1 }], affectedPharmacies: [{ pharmacyId: 'PH-04', name: 'P4', region: 'South', units: 4000, batches: ['B1'] }],
      affectedWarehouses: [], distributors: [], unaffectedPharmacies: [{ pharmacyId: 'PH-01', name: 'P1', region: 'North' }], totals: { batches: 1, batchUnits: 1, unitsDeliveredToPharmacies: 4000, pharmacies: 1, warehouses: 0, distributors: 0 },
      limitations: ['1 shipment leg(s) have no recorded destination'], graph: { nodes: [], edges: [] }, highlight: [] },
      '/api/recall': { recalls: [{ recallId: 'RCL-001', status: 'Active', reason: 'Sim', batches: 1 }] } })
    renderAt('/recall-analysis'); expect(await screen.findByText(/^AFFECTED PHARMACIES \(1\)/)).toBeTruthy(); expect(screen.getByText(/^UNAFFECTED PHARMACIES \(1\)/)).toBeTruthy(); expect(screen.getByText(/no recorded destination/)).toBeTruthy()
  })
  it('insights: shows live counts and profiling output', async () => {
    mockFetch({ '/api/insights': { totalNodes: 485, totalRelationships: 1394, nodesByLabel: [{ label: 'Batch', count: 40 }], relationshipsByType: [{ type: 'HAS_BATCH', count: 40 }], schemaTriples: [{ source: 'Medicine', type: 'HAS_BATCH', target: 'Batch', count: 40 }],
      topDegree: [], degreeStats: { min: 1, avg: 5.7, max: 30, nodes: 485 }, indexes: [], constraints: [], profiles: [{ title: 'Unique-index lookup', cypher: 'PROFILE MATCH (b) RETURN b', plan: { operator: 'ProduceResults', dbHits: 0, rows: 1, children: [] }, totalDbHits: 3, timing: { resultAvailableAfterMs: 2 }, rows: 1 }], note: 'measured live' } })
    renderAt('/database-insights'); expect(await screen.findByText('485')).toBeTruthy(); expect(screen.getByText('Unique-index lookup')).toBeTruthy(); expect(screen.getByText(/total dbHits 3/)).toBeTruthy()
  })
})

describe('background scene', () => {
  it('renders one decorative, aria-hidden layer that never takes part in interaction', () => {
    renderAt('/'); const scenes = screen.getAllByTestId('bg-scene'); expect(scenes).toHaveLength(1)
    expect(scenes[0].getAttribute('aria-hidden')).toBe('true'); expect(scenes[0].querySelectorAll('[role],a,button,input')).toHaveLength(0)
  })
  it('is the same DOM node after navigating to another page (persists, not remounted)', async () => {
    renderAt('/'); const before = screen.getByTestId('bg-scene')
    fireEvent.click(within(screen.getByRole('navigation', { name: 'Primary' })).getByText('MEDICINES')); await screen.findByText('Products')
    expect(screen.getByTestId('bg-scene')).toBe(before)
  })
})
