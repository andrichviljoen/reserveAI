import { useMemo, useState } from 'react'

export default function TriangleTable({ rows }) {
  const [sortKey, setSortKey] = useState('')
  const [dir, setDir] = useState('asc')

  const cols = useMemo(() => (rows?.length ? Object.keys(rows[0]) : []), [rows])
  const sorted = useMemo(() => {
    if (!sortKey) return rows || []
    return [...(rows || [])].sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av === bv) return 0
      return dir === 'asc' ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1)
    })
  }, [rows, sortKey, dir])

  const click = (c) => {
    if (sortKey === c) setDir(dir === 'asc' ? 'desc' : 'asc')
    setSortKey(c)
  }

  return (
    <div className="overflow-auto rounded-xl border bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-100">
          <tr>
            {cols.map((c) => (
              <th key={c} onClick={() => click(c)} className="cursor-pointer px-3 py-2 text-left font-medium text-slate-700">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <tr key={i} className="border-t">
              {cols.map((c) => (
                <td key={c} className="px-3 py-2">{`${r[c] ?? '-'}`}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}