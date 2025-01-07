import { useState } from 'react'
import { doReading, ReadingResult } from '@/api/tarot'

export const useTarotReading = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ReadingResult | null>(null)

  const performReading = async (question: string, spreadType: string) => {
    try {
      setLoading(true)
      setError(null)
      const readingResult = await doReading(question, spreadType)
      setResult(readingResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return {
    loading,
    error,
    result,
    performReading
  }
} 