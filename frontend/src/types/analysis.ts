export interface Position {
  ticker: string
  label: string | null
  quantity: number
  average_cost: number
  cost_basis: number
  current_price: number | null
  current_value: number | null
  unrealized_gain: number | null
  unrealized_gain_pct: number | null
  weight_pct: number | null
  sector: string | null
  country: string | null
  currency: string | null
  pe_ratio: number | null
  market_data_available: boolean
}

export interface PortfolioSummary {
  total_cost_basis: number
  total_current_value: number
  total_unrealized_gain: number
  total_unrealized_gain_pct: number
  realized_gain: number
  total_dividends: number
  total_fees: number
  positions_count: number
  as_of: string
}

export interface AllocationSlice {
  label: string
  value: number
  weight_pct: number
}

export interface PerformancePoint {
  date: string
  portfolio_value: number
  portfolio_return_pct: number
  benchmarks_return_pct: Record<string, number>
}

export interface RiskMetrics {
  annualized_volatility_pct: number | null
  sharpe_ratio: number | null
  max_drawdown_pct: number | null
  period_days: number
}

export interface AnalysisResponse {
  summary: PortfolioSummary
  positions: Position[]
  allocation_by_sector: AllocationSlice[]
  allocation_by_country: AllocationSlice[]
  allocation_by_ticker: AllocationSlice[]
  performance: PerformancePoint[]
  risk: RiskMetrics
  warnings: string[]
}
