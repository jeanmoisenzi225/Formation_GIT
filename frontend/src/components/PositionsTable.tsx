import type { Position } from '../types/analysis'
import { formatCurrency, formatNumber, formatPercent } from '../utils/format'
import { STATUS } from '../utils/colors'

interface Props {
  positions: Position[]
}

export function PositionsTable({ positions }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            {['Titre', 'Qté', 'PRU', 'Cours', 'Valeur', '+/- value', 'Poids', 'P/E', 'Secteur'].map((h) => (
              <th key={h} className="px-4 py-3 text-left font-semibold text-gray-600">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {positions.map((p) => {
            const gainColor = (p.unrealized_gain ?? 0) >= 0 ? STATUS.good : STATUS.critical
            return (
              <tr key={p.ticker} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{p.ticker}</div>
                  <div className="text-xs text-gray-500">{p.label ?? '—'}</div>
                  {!p.market_data_available && (
                    <div className="mt-0.5 text-xs text-amber-600">données de marché indisponibles</div>
                  )}
                </td>
                <td className="px-4 py-3 tabular-nums">{formatNumber(p.quantity)}</td>
                <td className="px-4 py-3 tabular-nums">{formatCurrency(p.average_cost, p.currency ?? 'XOF')}</td>
                <td className="px-4 py-3 tabular-nums">{formatCurrency(p.current_price, p.currency ?? 'XOF')}</td>
                <td className="px-4 py-3 tabular-nums font-medium">
                  {formatCurrency(p.current_value ?? p.cost_basis, p.currency ?? 'XOF')}
                </td>
                <td className="px-4 py-3 tabular-nums font-medium" style={{ color: p.market_data_available ? gainColor : undefined }}>
                  {p.market_data_available ? (
                    <>
                      {formatCurrency(p.unrealized_gain)}
                      <div className="text-xs font-normal">{formatPercent(p.unrealized_gain_pct)}</div>
                    </>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="px-4 py-3 tabular-nums">{p.weight_pct ? `${p.weight_pct.toFixed(1)} %` : '—'}</td>
                <td className="px-4 py-3 tabular-nums">{p.pe_ratio ? p.pe_ratio.toFixed(1) : '—'}</td>
                <td className="px-4 py-3 text-gray-600">{p.sector ?? '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
