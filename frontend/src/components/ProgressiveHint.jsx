import { useEffect, useState } from 'react'
import HintDisplay from './HintDisplay'

function ProgressiveHint({ hints, onReveal }) {
  const [hintIndex, setHintIndex] = useState(0)
  const [isOpen, setIsOpen] = useState(false)

  // Report the highest hint number the user has actually viewed (0 if never opened).
  useEffect(() => {
    if (isOpen) onReveal?.(hintIndex + 1)
  }, [isOpen, hintIndex, onReveal])

  if (!hints || hints.length === 0) {
    return null
  }

  const showNextHint = () => {
    if (hintIndex < hints.length - 1) {
      setHintIndex(hintIndex + 1)
    }
  }

  const showPrevHint = () => {
    if (hintIndex >= 1) {
      setHintIndex(hintIndex - 1)
    }
  }

  return (
    <div className="progressive-hint">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`hint-toggle ${isOpen ? 'open' : ''}`}
        type="button"
      >
        <span className="icon">💡</span>
        <span>Need a hint?</span>
        <span className="icon" style={{ marginLeft: 'auto' }}>
          {isOpen ? '▲' : '▼'}
        </span>
      </button>

      {isOpen && (
        <div className="hint-content">
          <HintDisplay>{hints[hintIndex]}</HintDisplay>

          <div className="hint-navigation">
            <button
              onClick={showPrevHint}
              type="button"
              disabled={hintIndex === 0}
              className="hint-nav-button"
            >
              ← Previous
            </button>

            <span className="hint-counter">
              {hintIndex + 1} / {hints.length}
            </span>

            <button
              onClick={showNextHint}
              type="button"
              disabled={hintIndex >= hints.length - 1}
              className="hint-nav-button"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProgressiveHint
