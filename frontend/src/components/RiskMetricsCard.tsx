import type { RiskMetrics } from '../types/analysis'
import { formatPercent } from '../utils/format'
import { STATUS } from '../utils/colors'

interface Props {
  risk: RiskMetrics
}

export function RiskMetricsCard({ risk }: Props) {
  const hasData = risk.annualized_volatility_pct !== null

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">Indicateurs de risque</h3>
      {!hasData ? (
        <p className="text-sm text-gray-400">Historique insuffisant pour calculer les indicateurs de risque.</p>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">Volatilité annualisée</p>
            <p className="mt-1 text-xl font-semibold text-gray-900">
              {formatPercent(risk.annualized_volatility_pct, 1)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">Ratio de Sharpe</p>
            <p className="mt-1 text-xl font-semibold" style={{ color: (risk.sharpe_ratio ?? 0) >= 0 ? STATUS.good : STATUS.critical }}>
              {risk.sharpe_ratio !== null ? risk.sharpe_ratio.toFixed(2) : '—'}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">Drawdown maximum</p>
            <p className="mt-1 text-xl font-semibold" style={{ color: STATUS.critical }}>
              {formatPercent(risk.max_drawdown_pct, 1)}
            </p>
          </div>
        </div>
      )}
      <p className="mt-4 text-xs text-gray-400">
        Calculés sur {risk.period_days} jours de cotation · taux sans risque supposé 2 %/an.
      </p>
    </div>
  )
}
