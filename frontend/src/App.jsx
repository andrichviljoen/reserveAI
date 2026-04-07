import { useMemo, useState } from 'react'
import { BarChart3, FileText, LogIn, Save } from 'lucide-react'
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ScatterChart, Scatter, BarChart, Bar,
} from 'recharts'
import MetricCard from './components/MetricCard'
import TriangleTable from './components/TriangleTable'
import DataMapping from './components/DataMapping'
import HeatmapTable from './components/HeatmapTable'
import { api } from './lib/api'

export default function App() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [openaiKey, setOpenaiKey] = useState('')
  const [user, setUser] = useState(null)
  const [context, setContext] = useState(null)
  const [notes, setNotes] = useState('')
  const [workspaces, setWorkspaces] = useState([])
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [uploadMeta, setUploadMeta] = useState(null)
  const [rows, setRows] = useState([])
  const [mapping, setMapping] = useState({ lob: '', origin: '', dev: '', value: '' })
  const [lineOfBusiness, setLineOfBusiness] = useState('')
  const [params, setParams] = useState({
    dataset_name: 'genins',
    data_type: 'Cumulative',
    date_format: 'YYYYQQ',
    method: 'Deterministic Chain Ladder',
    averaging_method: 'volume',
    drop_high: 0,
    drop_low: 0,
    bootstrap_simulations: 5000,
    confidence_level: 75,
  })

  const columns = useMemo(() => uploadMeta?.columns || [], [uploadMeta])
  const lobs = useMemo(() => {
    if (!rows.length || !mapping.lob) return []
    return [...new Set(rows.map((r) => r[mapping.lob]).filter(Boolean))]
  }, [rows, mapping])

  const login = async () => {
    const res = await api.post('/auth/login', { email, password })
    setUser(res.data.user)
    const ws = await api.get(`/auth/workspaces/${res.data.user.id}`)
    setWorkspaces(ws.data)
  }

  const handleFile = async (file) => {
    const b64 = await fileToBase64(file)
    const payload = {
      user_id: user.id,
      file_name: file.name,
      file_type: file.type || (file.name.endsWith('.csv') ? 'csv' : 'xlsx'),
      file_base64: b64.split(',')[1],
    }
    const res = await api.post('/upload', payload)
    setUploadMeta(res.data)
    setRows(res.data.preview)
    const cols = res.data.columns
    setMapping({ lob: cols[0], origin: cols[1], dev: cols[2], value: cols[3] })
  }

  const runAnalysis = async () => {
    const payload = uploadMeta ? {
      ...params,
      dataset_name: null,
      records: rows,
      line_of_business: lineOfBusiness,
      mapping,
    } : params
    const res = await api.post('/analyze', payload)
    setContext(res.data)
  }

  const saveWorkspace = async () => {
    const workspace_name = prompt('Workspace name') || ''
    if (!workspace_name || !context) return
    await api.post('/auth/workspaces/save', { user_id: user.id, workspace_name, context_data: context.context_data })
    const ws = await api.get(`/auth/workspaces/${user.id}`)
    setWorkspaces(ws.data)
  }

  const askChat = async () => {
    const next = [...messages, { role: 'user', content: chatInput }]
    setMessages(next)
    setChatInput('')
    const res = await api.post('/chat', {
      context_data: context?.context_data || {},
      actuary_notes: notes,
      messages: next,
      openai_api_key: openaiKey,
    })
    setMessages([...next, { role: 'assistant', content: res.data.content }])
  }

  const generateReport = async (type) => {
    const res = await api.post('/generate-report', {
      report_type: type,
      context_data: context,
      actuary_notes: notes,
      openai_api_key: openaiKey,
    })
    const a = document.createElement('a')
    a.href = `data:${res.data.media_type};base64,${res.data.file_base64}`
    a.download = res.data.file_name
    a.click()
  }

  if (!user) {
    return <div className="mx-auto mt-24 max-w-sm rounded-xl border bg-white p-6 shadow">
      <h1 className="mb-4 text-xl font-semibold">AI Actuarial Reserving Suite</h1>
      <input className="mb-2 w-full rounded border p-2" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input className="mb-4 w-full rounded border p-2" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={login} className="flex w-full items-center justify-center gap-2 rounded bg-slate-900 p-2 text-white"><LogIn size={16} /> Login</button>
    </div>
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-80 space-y-3 border-r bg-slate-900 p-4 text-white">
        <h2 className="text-lg font-semibold">Cloud Workspaces</h2>
        <select className="w-full rounded bg-slate-800 p-2" onChange={(e) => {
          const sel = workspaces.find((w) => w.workspace_name === e.target.value)
          if (sel) setContext({ context_data: sel.context_data, ...sel.context_data })
        }}>
          <option>Create New Analysis</option>
          {workspaces.map((w) => <option key={w.workspace_name}>{w.workspace_name}</option>)}
        </select>
        <input className="w-full rounded bg-slate-800 p-2" placeholder="OpenAI API Key" type="password" value={openaiKey} onChange={(e) => setOpenaiKey(e.target.value)} />
        <input type="file" accept=".csv,.xlsx" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
        <select className="w-full rounded bg-slate-800 p-2" value={params.method} onChange={(e) => setParams({ ...params, method: e.target.value })}>
          <option>Deterministic Chain Ladder</option><option>Bootstrap ODP</option>
        </select>
        <button onClick={runAnalysis} className="flex w-full items-center justify-center gap-2 rounded bg-indigo-500 p-2"><BarChart3 size={16} />Analyze</button>
        <button onClick={saveWorkspace} className="flex w-full items-center justify-center gap-2 rounded bg-emerald-500 p-2"><Save size={16} />Save Workspace</button>
        <button onClick={() => generateReport('word')} className="flex w-full items-center justify-center gap-2 rounded bg-slate-700 p-2"><FileText size={16} />Word</button>
        <button onClick={() => generateReport('excel')} className="w-full rounded bg-slate-700 p-2">Excel</button>
        <textarea rows={5} className="w-full rounded bg-slate-800 p-2" placeholder="Actuary notes" value={notes} onChange={(e) => setNotes(e.target.value)} />

        <div className="rounded bg-slate-800 p-2">
          <h4 className="mb-2 text-sm font-semibold">A(I)ctuary Chat</h4>
          <div className="max-h-40 space-y-2 overflow-auto text-xs">
            {messages.map((m, i) => <div key={i}><b>{m.role}:</b> {m.content}</div>)}
          </div>
          <input className="mt-2 w-full rounded bg-slate-700 p-1" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Ask..." />
          <button onClick={askChat} className="mt-2 w-full rounded bg-indigo-500 p-1">Send</button>
        </div>
      </aside>

      <main className="flex-1 space-y-4 p-6">
        {uploadMeta && <DataMapping columns={columns} mapping={mapping} onChange={setMapping} lineOfBusiness={lineOfBusiness} setLineOfBusiness={setLineOfBusiness} lobs={lobs} />}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <MetricCard label="Total IBNR" value={context?.metrics?.total_ibnr} />
          <MetricCard label="Total Ultimate" value={context?.metrics?.total_ultimate} />
          <MetricCard label="Risk Margin" value={context?.metrics?.risk_margin} />
        </div>

        <HeatmapTable rows={context?.tables?.link_ratios || []} />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl border bg-white p-4"><h3 className="mb-2 font-medium">AvE Analysis</h3><div className="h-64"><ResponsiveContainer width="100%" height="100%"><ScatterChart><CartesianGrid /><XAxis dataKey="Expected" /><YAxis dataKey="Actual" /><Tooltip /><Scatter data={context?.diagnostics?.ave?.data || []} fill="#2563eb" /></ScatterChart></ResponsiveContainer></div></div>
          <div className="rounded-xl border bg-white p-4"><h3 className="mb-2 font-medium">Bootstrap LDF Distribution</h3><div className="h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={context?.diagnostics?.bootstrap?.ldf_histogram?.data || []}><CartesianGrid /><XAxis dataKey="value" hide /><YAxis /><Tooltip /><Bar dataKey="value" fill="#7c3aed" /></BarChart></ResponsiveContainer></div></div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {['by_dev', 'by_origin', 'by_valuation', 'scatter'].map((k) => (
            <div key={k} className="rounded-xl border bg-white p-4">
              <h3 className="mb-2 text-sm font-medium">Residuals {k}</h3>
              <div className="h-48"><ResponsiveContainer width="100%" height="100%"><LineChart data={context?.diagnostics?.residuals?.[k] || []}><CartesianGrid /><Tooltip /><Line type="monotone" dataKey={Object.keys((context?.diagnostics?.residuals?.[k] || [])[0] || {}).find((x) => !['index', 'origin', 'development', 'valuation'].includes(x))} stroke="#ef4444" /></LineChart></ResponsiveContainer></div>
            </div>
          ))}
        </div>

        <TriangleTable rows={context?.tables?.triangle || []} />
      </main>
    </div>
  )
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
  })
}
