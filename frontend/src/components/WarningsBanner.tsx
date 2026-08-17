interface Props {
  warnings: string[]
}

export function WarningsBanner({ warnings }: Props) {
  if (warnings.length === 0) return null

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
      <p className="mb-1 font-semibold">Avertissements ({warnings.length})</p>
      <ul className="list-inside list-disc space-y-0.5">
        {warnings.map((w, i) => (
          <li key={i}>{w}</li>
        ))}
      </ul>
    </div>
  )
}
