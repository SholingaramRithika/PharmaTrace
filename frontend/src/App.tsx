import React from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './Layout'
import Home from './pages/Home'
import CommandCenter from './pages/CommandCenter'
import GraphExplorer from './pages/GraphExplorer'
import Medicines from './pages/Medicines'
import Traceability from './pages/Traceability'
import RiskIntelligence from './pages/RiskIntelligence'
import RecallAnalysis from './pages/RecallAnalysis'
import DatabaseLab from './pages/DatabaseLab'
import DatabaseInsights from './pages/DatabaseInsights'
import { Stub } from './pages/Stub'


export default function App() {
  return <Routes><Route element={<Layout />}>
    <Route index element={<Home />} />
    <Route path="command-center" element={<CommandCenter />} />
    <Route path="graph-explorer" element={<GraphExplorer />} />
    <Route path="medicines" element={<Medicines />} />
    <Route path="traceability" element={<Traceability />} />
    <Route path="risk-intelligence" element={<RiskIntelligence />} />
    <Route path="recall-analysis" element={<RecallAnalysis />} />
    <Route path="database-lab" element={<DatabaseLab />} />
    <Route path="database-insights" element={<DatabaseInsights />} />
    <Route path="*" element={<Stub title="Page not found" />} />
  </Route></Routes>
}
