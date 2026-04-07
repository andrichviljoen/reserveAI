export default function HeatmapTable({ rows }) {
  if (!rows?.length) return null
  const cols = Object.keys(rows[0])
  const numericVals = rows.flatMap((r) => cols.map((c) => Number(r[c])).filter((v) => !Number.isNaN(v)))
  const min = Math.min(...numericVals)
  const max = Math.max(...numericVals)
  const color = (v) => {
    const n = (Number(v) - min) / ((max - min) || 1)
    const alpha = 0.1 + (0.7 * n)
    return `rgba(234,88,12,${alpha})`
  }
  return (
    <div className="overflow-auto rounded-xl border bg-white p-2">
      <h3 className="mb-2 px-1 font-medium">Link Ratio Heatmap</h3>
      <table className="min-w-full text-sm">
        <thead><tr>{cols.map((c) => <th key={c} className="px-2 py-1 text-left">{c}</th>)}</tr></thead>
        <tbody>
          {rows.slice(0, 50).map((r, i) => (
            <tr key={i} className="border-t">
              {cols.map((c) => (
                <td key={c} className="px-2 py-1" style={{ backgroundColor: Number.isNaN(Number(r[c])) ? 'transparent' : color(r[c]) }}>{`${r[c] ?? '-'}`}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
