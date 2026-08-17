import { useState } from 'react'
import { analyzeStatement } from './api/client'
import { FileUpload } from './components/FileUpload'
import { SummaryCards } from './components/SummaryCards'
import { PositionsTable } from './components/PositionsTable'
import { AllocationPieChart } from './components/AllocationPieChart'
import { PerformanceChart } from './components/PerformanceChart'
import { RiskMetricsCard } from './components/RiskMetricsCard'
import { WarningsBanner } from './components/WarningsBanner'
import type { AnalysisResponse } from './types/analysis'

function App() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)

  const handleFile = async (file: File) => {
    setIsLoading(true)
    setError(null)
    setFileName(file.name)
    try {
      const result = await analyzeStatement(file)
      setAnalysis(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur inconnue s'est produite.")
      setAnalysis(null)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <h1 className="text-xl font-bold text-gray-900">📈 Analyseur de portefeuille titres</h1>
          <p className="mt-1 text-sm text-gray-500">
            Importez un relevé de compte-titres pour confronter vos positions aux données de marché.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <FileUpload onFileSelected={handleFile} isLoading={isLoading} />

        {fileName && !isLoading && (
          <p className="text-sm text-gray-500">
            Fichier analysé : <span className="font-medium text-gray-700">{fileName}</span>
          </p>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}

        {analysis && (
          <div className="space-y-6">
            <WarningsBanner warnings={analysis.warnings} />
            <SummaryCards summary={analysis.summary} />

            <PerformanceChart data={analysis.performance} />

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <AllocationPieChart title="Répartition par secteur" data={analysis.allocation_by_sector} />
              <AllocationPieChart title="Répartition par zone géographique" data={analysis.allocation_by_country} />
            </div>

            <RiskMetricsCard risk={analysis.risk} />

            <div>
              <h2 className="mb-3 text-sm font-semibold text-gray-700">Détail des positions</h2>
              <PositionsTable positions={analysis.positions} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
