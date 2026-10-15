const ROWS = [
  { key: 'High', bar: 'bg-red-500', text: 'text-red-700' },
  { key: 'Medium', bar: 'bg-amber-500', text: 'text-amber-700' },
  { key: 'Low', bar: 'bg-green-500', text: 'text-green-700' },
]

export default function ConfidenceChart({ confidence }) {
  return (
    <div className="space-y-3">
      {ROWS.map(({ key, bar, text }) => {
        const pct = Math.round((confidence?.[key] || 0) * 100)
        return (
          <div key={key}>
            <div className="mb-1 flex items-center justify-between text-sm font-semibold">
              <span>{key} risk</span>
              <span className={text}>{pct}%</span>
            </div>
            <div className="h-4 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className={`h-4 rounded-full ${bar}`}
                style={{ width: `${Math.max(pct, 1)}%` }}
                role="img"
                aria-label={`${key} risk confidence ${pct}%`}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
