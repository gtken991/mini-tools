import { useState } from 'react'
import type { TarotCard as TarotCardType } from '../api/tarot'
import './TarotCard.css'

interface TarotCardProps {
  card: TarotCardType
  isRevealed?: boolean
  onReveal?: () => void
  isImageLoaded?: boolean
}

export const TarotCard: React.FC<TarotCardProps> = ({
  card,
  isRevealed = true,
  onReveal,
  isImageLoaded = false
}) => {
  const [isFlipped, setIsFlipped] = useState(!isRevealed)

  const handleClick = () => {
    if (!isRevealed && onReveal) {
      setIsFlipped(false)
      onReveal()
    }
  }

  return (
    <div
      className={`tarot-card ${isFlipped ? 'flipped' : ''} ${
        card.reversed ? 'reversed' : ''
      } ${!isImageLoaded ? 'loading' : ''}`}
      onClick={handleClick}
    >
      <div className="tarot-card-inner">
        <div className="tarot-card-front">
          {isImageLoaded ? (
            <img src={card.image} alt={card.name} className="card-image" />
          ) : (
            <div className="card-placeholder">
              <div className="loading-spinner" />
            </div>
          )}
          <div className="card-info">
            <h3 className="card-name">{card.name}</h3>
            {card.reversed && <span className="card-position">逆位</span>}
          </div>
        </div>
        <div className="tarot-card-back">
          <img
            src="/images/cards/card_back.jpg"
            alt="Card Back"
            className="card-back-image"
          />
        </div>
      </div>
    </div>
  )
} 