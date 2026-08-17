import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { AllocationSlice } from '../types/analysis'
import { categoricalColor } from '../utils/colors'
import { formatCurrency } from '../utils/format'

interface Props {
  title: string
  data: AllocationSlice[]
  maxSlices?: number
}

export function AllocationPieChart({ title, data, maxSlices = 8 }: Props) {
  const sorted = [...data].sort((a, b) => b.value - a.value)
  const top = sorted.slice(0, maxSlices)
  const rest = sorted.slice(maxSlices)
  const chartData =
    rest.length > 0
      ? [...top, { label: 'Autres', value: rest.reduce((s, r) => s + r.value, 0), weight_pct: rest.reduce((s, r) => s + r.weight_pct, 0) }]
      : top

  if (chartData.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-gray-700">{title}</h3>
        <p className="text-sm text-gray-400">Pas de données disponibles.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="label" innerRadius={55} outerRadius={90} paddingAngle={2}>
            {chartData.map((entry, index) => (
              <Cell key={entry.label} fill={index === top.length && rest.length > 0 ? '#c3c2b7' : categoricalColor(index)} stroke="#fcfcfb" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, _name, entry) => [
              `${formatCurrency(Number(value))} (${entry.payload.weight_pct.toFixed(1)} %)`,
              entry.payload.label,
            ]}
          />
          <Legend layout="vertical" align="right" verticalAlign="middle" wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
