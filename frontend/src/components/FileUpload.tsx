import { useRef, useState } from 'react'

interface Props {
  onFileSelected: (file: File) => void
  isLoading: boolean
}

export function FileUpload({ onFileSelected, isLoading }: Props) {
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return
    onFileSelected(files[0])
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragOver(true)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragOver(false)
        handleFiles(e.dataTransfer.files)
      }}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
        isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.txt"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="mb-3 text-4xl">📊</div>
      <p className="text-lg font-semibold text-gray-800">
        {isLoading ? 'Analyse en cours…' : 'Déposez votre relevé de compte-titres (CSV)'}
      </p>
      <p className="mt-1 text-sm text-gray-500">ou cliquez pour parcourir vos fichiers</p>
      <p className="mt-4 text-xs text-gray-400">
        Colonnes attendues : date, ticker, type (achat/vente/dividende), quantité, prix
      </p>
      <p className="mt-1 text-xs text-gray-400">
        Titres BRVM (ex. ECOC, SNTS, SDCC) reconnus nativement — autres places boursières en repli
      </p>
    </div>
  )
}
