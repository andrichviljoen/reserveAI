export default function MetricCard({ label, value }) {
  return (
    <div className="rounded-xl border bg-white p-4 shadow-sm">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-800">{value ?? '-'}</p>
    </div>
  )
}
