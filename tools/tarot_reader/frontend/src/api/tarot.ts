import axios from 'axios'

export interface TarotCard {
  id: number
  name: string
  image: string
  meaning: string
  reversed: boolean
}

export interface ReadingResult {
  cards: TarotCard[]
  result: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

// 使用本地图片
const IMAGE_BASE = '/images/cards'

// 卡牌图片映射
export const cardImageMap: { [key: string]: string } = {
  // Major Arcana (大阿卡纳)
  'the_fool': `${IMAGE_BASE}/the_fool.jpg`,
  'the_magician': `${IMAGE_BASE}/the_magician.jpg`,
  'the_high_priestess': `${IMAGE_BASE}/the_high_priestess.jpg`,
  'the_empress': `${IMAGE_BASE}/the_empress.jpg`,
  'the_emperor': `${IMAGE_BASE}/the_emperor.jpg`,
  'the_hierophant': `${IMAGE_BASE}/the_hierophant.jpg`,
  'the_lovers': `${IMAGE_BASE}/the_lovers.jpg`,
  'the_chariot': `${IMAGE_BASE}/the_chariot.jpg`,
  'strength': `${IMAGE_BASE}/strength.jpg`,
  'the_hermit': `${IMAGE_BASE}/the_hermit.jpg`,
  'wheel_of_fortune': `${IMAGE_BASE}/wheel_of_fortune.jpg`,
  'justice': `${IMAGE_BASE}/justice.jpg`,
  'the_hanged_man': `${IMAGE_BASE}/the_hanged_man.jpg`,
  'death': `${IMAGE_BASE}/death.jpg`,
  'temperance': `${IMAGE_BASE}/temperance.jpg`,
  'the_devil': `${IMAGE_BASE}/the_devil.jpg`,
  'the_tower': `${IMAGE_BASE}/the_tower.jpg`,
  'the_star': `${IMAGE_BASE}/the_star.jpg`,
  'the_moon': `${IMAGE_BASE}/the_moon.jpg`,
  'the_sun': `${IMAGE_BASE}/the_sun.jpg`,
  'judgement': `${IMAGE_BASE}/judgement.jpg`,
  'the_world': `${IMAGE_BASE}/the_world.jpg`,
  
  // 默认卡背
  'card_back': `${IMAGE_BASE}/card_back.jpg`
} as const

export const getCardImage = (cardName: string): string => {
  const key = cardName.toLowerCase().replace(/\s+/g, '_')
  return cardImageMap[key] || cardImageMap.card_back
}

export const doReading = async (
  question: string,
  spreadType: string
): Promise<ReadingResult> => {
  const response = await axios.post(
    `${API_BASE_URL}/api/reading`,
    null,
    {
      params: {
        question,
        spread_type: spreadType
      }
    }
  )
  
  // 处理返回的卡牌数据，添加正确的图片路径
  const result = response.data
  result.cards = result.cards.map((card: TarotCard) => ({
    ...card,
    image: getCardImage(card.name)
  }))
  
  return result
}
