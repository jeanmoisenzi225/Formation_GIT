import type { PortfolioSummary } from '../types/analysis'
import { formatCurrency, formatPercent } from '../utils/format'
import { STATUS } from '../utils/colors'

interface Props {
  summary: PortfolioSummary
}

function Card({ label, value, sub, deltaColor }: { label: string; value: string; sub?: string; deltaColor?: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
      {sub && (
        <p className="mt-1 text-sm font-medium" style={{ color: deltaColor }}>
          {sub}
        </p>
      )}
    </div>
  )
}

export function SummaryCards({ summary }: Props) {
  const gainColor = summary.total_unrealized_gain >= 0 ? STATUS.good : STATUS.critical

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card label="Valeur actuelle" value={formatCurrency(summary.total_current_value)} />
      <Card label="Coût d'acquisition" value={formatCurrency(summary.total_cost_basis)} />
      <Card
        label="Plus/moins-value latente"
        value={formatCurrency(summary.total_unrealized_gain)}
        sub={formatPercent(summary.total_unrealized_gain_pct)}
        deltaColor={gainColor}
      />
      <Card label="Positions" value={String(summary.positions_count)} />
      <Card label="Plus-values réalisées" value={formatCurrency(summary.realized_gain)} />
      <Card label="Dividendes perçus" value={formatCurrency(summary.total_dividends)} />
      <Card label="Frais payés" value={formatCurrency(summary.total_fees)} />
      <Card label="Date d'analyse" value={new Date(summary.as_of).toLocaleDateString('fr-FR')} />
    </div>
  )
}
