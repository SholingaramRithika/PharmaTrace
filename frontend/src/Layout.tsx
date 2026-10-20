import { NavLink, Outlet } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from './theme'
import { useApi } from './api'
import { useEffect, useState } from 'react'
import BackgroundScene from './background/BackgroundScene'

const NAV = [['/', 'Home'], ['/command-center', 'Command Center'], ['/graph-explorer', 'Graph Explorer'], ['/medicines', 'Medicines'], ['/traceability', 'Traceability'],
  ['/risk-intelligence', 'Risk Intelligence'], ['/recall-analysis', 'Recall Analysis'], ['/database-lab', 'Database Lab'], ['/database-insights', 'Insights']]

function Status() {
  const [tick, setTick] = useState(0); useEffect(() => { const t = setInterval(() => setTick(x => x + 1), 15000); return () => clearInterval(t) }, [])
  const { data, error, loading } = useApi<{ database: { connected: boolean; nodes?: number } }>(`/api/health?t=${tick}`)
  const ok = data?.database.connected
  return <span className="flex items-center gap-2 font-mono text-[11px] tracking-wider" role="status" aria-live="polite">
    <i className={`w-2 h-2 rounded-full ${loading && !data ? 'bg-mute' : ok ? 'bg-emerald-400' : 'bg-coral'}`} />
    {loading && !data ? 'CHECKING…' : ok ? `NEO4J CONNECTED · ${data!.database.nodes} NODES` : error ? 'API OFFLINE' : 'NEO4J DISCONNECTED'}</span>
}

export default function Layout() {
  const { theme, toggle } = useTheme()
  return <div className="relative isolate min-h-screen">
    <BackgroundScene />
    <div className="relative z-10 min-h-screen flex flex-col">
    <header className="border-b border-line bg-bg/90 backdrop-blur sticky top-0 z-30">
      <div className="max-w-[1500px] mx-auto px-4 py-3 flex items-center gap-4">
        <NavLink to="/" className="flex items-center gap-2 shrink-0"><img src="/logo.svg" alt="" className="w-8 h-8" /><span className="font-head font-bold tracking-widest">PHARMATRACE</span></NavLink>
        <nav aria-label="Primary" className="flex-1 flex gap-1 overflow-x-auto">
          {NAV.map(([to, l]) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) =>
            `px-2.5 py-1.5 rounded text-[11px] font-mono tracking-wider whitespace-nowrap ${isActive ? 'bg-panel text-accent border border-accent' : 'text-mute hover:text-ink border border-transparent'}`}>{l.toUpperCase()}</NavLink>)}
        </nav>
        <Status />
        <button onClick={toggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} aria-pressed={theme === 'light'}
          className="flex items-center gap-2 px-3 py-1.5 rounded border border-line hover:border-accent text-xs font-mono">
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}{theme === 'dark' ? 'LIGHT' : 'DARK'}</button>
      </div>
    </header>
    <main className="flex-1"><Outlet /></main>
    <footer className="border-t border-line px-4 py-4 text-center font-mono text-[11px] text-mute">PharmaTrace · academic DBMS case study · Neo4j · all data synthetic &amp; fictional · product images illustrative only</footer>
    </div>
  </div>
}
