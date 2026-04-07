import { useEffect, useState } from 'react'
import { BarChart3, FileText, LogIn, Save } from 'lucide-react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import MetricCard from './components/MetricCard'
import TriangleTable from './components/TriangleTable'
import { api } from './lib/api'

export default function App() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [user, setUser] = useState(null)
  const [notes, setNotes] = useState('')
  const [context, setContext] = useState(null)
  const [params, setParams] = useState({
    dataset_name: 'genins',
    method: 'Deterministic Chain Ladder',
    averaging_method: 'volume',
    drop_high: 0,
    drop_low: 0,
    bootstrap_simulations: 5000,
    confidence_level: 75,
    data_type: 'Cumulative',
    date_format: 'YYYYQQ',
  })

  useEffect(() => {
    if (user) runAnalysis()
  }, [params.method])

  const login = async () => {
    const res = await api.post('/auth/login', { email, password })
    setUser(res.data.user)
  }

  const runAnalysis = async () => {
    const res = await api.post('/analyze', params)
    setContext(res.data)
  }

  const saveWorkspace = async () => {
    if (!user || !context) return
    await api.post('/auth/workspaces/save', {
      user_id: user.id,
      workspace_name: `analysis-${new Date().toISOString()}`,
      context_data: context,
    })
  }

  const generateReport = async (reportType) => {
    const res = await api.post('/generate-report', {
      report_type: reportType,
      context_data: context,
      actuary_notes: notes,
    })
    const a = document.createElement('a')
    a.href = `data:${res.data.media_type};base64,${res.data.file_base64}`
    a.download = res.data.file_name
    a.click()
  }

  if (!user) {
    return (
      <div className="mx-auto mt-24 max-w-sm rounded-xl border bg-white p-6 shadow">
        <h1 className="mb-4 text-xl font-semibold">AI Actuarial Suite</h1>
        <input className="mb-2 w-full rounded border p-2" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        <input className="mb-4 w-full rounded border p-2" type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
        <button onClick={login} className="flex w-full items-center justify-center gap-2 rounded bg-slate-900 p-2 text-white"><LogIn size={16} /> Login</button>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-72 border-r bg-slate-900 p-4 text-white">
        <h2 className="mb-4 text-lg font-semibold">ReserveAI</h2>
        <label className="mb-1 block text-xs">Method</label>
        <select className="mb-3 w-full rounded bg-slate-800 p-2" value={params.method} onChange={(e) => setParams({ ...params, method: e.target.value })}>
          <option>Deterministic Chain Ladder</option>
          <option>Bootstrap ODP</option>
        </select>
        <button onClick={runAnalysis} className="mb-2 flex w-full items-center justify-center gap-2 rounded bg-indigo-500 p-2"><BarChart3 size={16} /> Analyze</button>
        <button onClick={saveWorkspace} className="mb-2 flex w-full items-center justify-center gap-2 rounded bg-emerald-500 p-2"><Save size={16} /> Save Workspace</button>
        <button onClick={() => generateReport('word')} className="mb-2 flex w-full items-center justify-center gap-2 rounded bg-slate-700 p-2"><FileText size={16} /> Word Report</button>
        <button onClick={() => generateReport('excel')} className="mb-2 flex w-full items-center justify-center gap-2 rounded bg-slate-700 p-2">Excel Report</button>
        <textarea className="mt-2 w-full rounded bg-slate-800 p-2 text-sm" rows={5} placeholder="Actuary notes" onChange={(e) => setNotes(e.target.value)} />
      </aside>

      <main className="flex-1 space-y-4 p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Actuarial Reserving Dashboard</h1>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <MetricCard label="Total IBNR" value={context?.metrics?.total_ibnr?.toLocaleString?.() || context?.metrics?.total_ibnr} />
          <MetricCard label="Total Ultimate" value={context?.metrics?.total_ultimate?.toLocaleString?.() || context?.metrics?.total_ultimate} />
          <MetricCard label="Bootstrap Mean IBNR" value={context?.metrics?.bootstrap_mean_ibnr?.toLocaleString?.() || '-'} />
        </div>

        <div className="rounded-xl border bg-white p-4">
          <h3 className="mb-2 font-medium">Development Trend (Interactive)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={context?.charts?.triangle_development?.data || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="origin" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey={context?.charts?.triangle_development?.series?.[0]} stroke="#4f46e5" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <section>
          <h3 className="mb-2 font-medium">Loss Triangle (Sortable)</h3>
          <TriangleTable rows={context?.tables?.triangle || []} />
        </section>
      </main>
    </div>
  )
}
