import { useEffect, useState } from 'react'
import { cardImageMap } from '../api/tarot'

export interface PreloadStatus {
  isComplete: boolean
  progress: number
  loadedImages: { [key: string]: boolean }
  errors: { [key: string]: string }
  hasErrors: boolean
}

export const useImagePreload = () => {
  const [status, setStatus] = useState<PreloadStatus>({
    isComplete: false,
    progress: 0,
    loadedImages: {},
    errors: {},
    hasErrors: false
  })

  useEffect(() => {
    let isMounted = true
    const imageUrls = Object.entries(cardImageMap)
    let loadedCount = 0
    let errorCount = 0
    const totalImages = imageUrls.length
    const loadedImages: { [key: string]: boolean } = {}
    const errors: { [key: string]: string } = {}

    const updateStatus = () => {
      if (!isMounted) return
      const progress = Math.round(((loadedCount + errorCount) / totalImages) * 100)
      setStatus({
        isComplete: loadedCount + errorCount === totalImages,
        progress,
        loadedImages,
        errors,
        hasErrors: errorCount > 0
      })
    }

    const loadImage = (key: string, url: string): Promise<void> => {
      return new Promise((resolve) => {
        const img = new Image()
        let isResolved = false

        const finishLoading = () => {
          if (!isResolved) {
            isResolved = true
            resolve()
          }
        }
        
        const timeout = setTimeout(() => {
          if (!isMounted) return
          img.src = ''  // 停止加载
          errorCount++
          errors[key] = `加载超时: ${url}`
          updateStatus()
          finishLoading()
        }, 10000) // 10秒超时

        img.onload = () => {
          if (!isMounted) return
          clearTimeout(timeout)
          loadedCount++
          loadedImages[key] = true
          updateStatus()
          finishLoading()
        }

        img.onerror = () => {
          if (!isMounted) return
          clearTimeout(timeout)
          errorCount++
          errors[key] = `无法加载图片: ${url}`
          updateStatus()
          finishLoading()
        }

        img.src = url
      })
    }

    // 首先加载卡背图片
    loadImage('card_back', cardImageMap.card_back)
      .then(() => {
        if (!isMounted) return
        // 并行加载其他图片，但限制并发数
        const batchSize = 3
        const otherImages = imageUrls.filter(([key]) => key !== 'card_back')
        
        const loadBatch = async (batch: [string, string][]) => {
          if (!isMounted) return
          await Promise.all(batch.map(([key, url]) => loadImage(key, url)))
        }

        const loadAllImages = async () => {
          for (let i = 0; i < otherImages.length; i += batchSize) {
            if (!isMounted) return
            const batch = otherImages.slice(i, i + batchSize)
            await loadBatch(batch)
          }
        }

        return loadAllImages()
      })
      .catch((error) => {
        if (!isMounted) return
        console.error('图片预加载出错:', error)
      })

    return () => {
      isMounted = false
    }
  }, [])

  return status
} 