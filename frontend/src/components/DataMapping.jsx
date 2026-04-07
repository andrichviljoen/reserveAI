export default function DataMapping({ columns, mapping, onChange, lineOfBusiness, setLineOfBusiness, lobs }) {
  const update = (key, value) => onChange({ ...mapping, [key]: value })
  return (
    <div className="rounded-xl border bg-white p-4">
      <h3 className="mb-3 font-medium">Data Mapping</h3>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {['lob', 'origin', 'dev', 'value'].map((k) => (
          <label key={k} className="text-sm">
            <span className="mb-1 block capitalize">{k} column</span>
            <select className="w-full rounded border p-2" value={mapping[k] || ''} onChange={(e) => update(k, e.target.value)}>
              {columns.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
        ))}
        <label className="text-sm md:col-span-2">
          <span className="mb-1 block">Line of Business</span>
          <select className="w-full rounded border p-2" value={lineOfBusiness || ''} onChange={(e) => setLineOfBusiness(e.target.value)}>
            {lobs.map((l) => <option key={l}>{l}</option>)}
          </select>
        </label>
      </div>
    </div>
  )
}
