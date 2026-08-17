import axios from 'axios'
import type { AnalysisResponse } from '../types/analysis'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export async function analyzeStatement(file: File): Promise<AnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const { data } = await axios.post<AnalysisResponse>(`${API_BASE_URL}/api/analyze`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      throw new Error(error.response.data.detail as string)
    }
    throw new Error("Impossible de contacter l'API d'analyse. Vérifiez que le backend est démarré.")
  }
}
