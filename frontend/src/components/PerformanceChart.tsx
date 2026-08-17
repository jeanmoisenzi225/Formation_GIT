import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { PerformancePoint } from '../types/analysis'
import { CATEGORICAL, CHROME } from '../utils/colors'
import { formatPercent } from '../utils/format'

interface Props {
  data: PerformancePoint[]
}

export function PerformanceChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-gray-700">Performance vs marché</h3>
        <p className="text-sm text-gray-400">
          Historique de prix indisponible pour tracer la courbe de performance.
        </p>
      </div>
    )
  }

  const benchmarkNames = Array.from(new Set(data.flatMap((p) => Object.keys(p.benchmarks_return_pct))))

  const chartData = data.map((p) => ({
    date: p.date,
    Portefeuille: p.portfolio_return_pct,
    ...Object.fromEntries(benchmarkNames.map((name) => [name, p.benchmarks_return_pct[name] ?? null])),
  }))

  const series = ['Portefeuille', ...benchmarkNames]

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">Performance vs marché (base 100, %)</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHROME.gridline} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: CHROME.textMuted }}
            stroke={CHROME.axis}
            tickFormatter={(d: string) => new Date(d).toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' })}
            minTickGap={40}
          />
          <YAxis tick={{ fontSize: 11, fill: CHROME.textMuted }} stroke={CHROME.axis} tickFormatter={(v: number) => `${v}%`} />
          <Tooltip
            formatter={(value) => formatPercent(Number(value))}
            labelFormatter={(d) => new Date(String(d)).toLocaleDateString('fr-FR')}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((name, index) => (
            <Line
              key={name}
              type="monotone"
              dataKey={name}
              stroke={CATEGORICAL[index]}
              strokeWidth={name === 'Portefeuille' ? 2.5 : 2}
              dot={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
