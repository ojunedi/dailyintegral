import { useEffect, useState } from 'react'
import HintDisplay from './HintDisplay'
import { apiService } from '../services/api'

function ProgressiveHint({ hints, onReveal, problem, attempt }) {
  const [hintIndex, setHintIndex] = useState(0)
  const [isOpen, setIsOpen] = useState(false)
  const [aiHint, setAiHint] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState(null)

  // Report the number of hints actually viewed: highest static hint reached,
  // plus one if the AI hint was used (0 if never opened).
  useEffect(() => {
    const viewed = (isOpen ? hintIndex + 1 : 0) + (aiHint ? 1 : 0)
    if (viewed > 0) onReveal?.(viewed)
  }, [isOpen, hintIndex, aiHint, onReveal])

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

  const fetchAiHint = async () => {
    setAiLoading(true)
    setAiError(null)
    try {
      const response = await apiService.getAiHint(attempt, problem)
      if (response.success) {
        setAiHint(response.hint)
      } else {
        setAiError(response.error || 'Could not generate a hint')
      }
    } catch (err) {
      setAiError(err.message)
    } finally {
      setAiLoading(false)
    }
  }

  const hasAttempt = Boolean(attempt?.trim())

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

          {problem && (
            <div className="ai-hint">
              {aiHint && (
                <div className="ai-hint-result">
                  <HintDisplay>{aiHint}</HintDisplay>
                </div>
              )}
              <button
                onClick={fetchAiHint}
                type="button"
                disabled={aiLoading}
                className="hint-nav-button ai-hint-button"
              >
                {aiLoading
                  ? 'Thinking…'
                  : aiHint
                    ? '🤖 Re-analyze'
                    : hasAttempt
                      ? '🤖 Analyze my attempt'
                      : '🤖 Get a smart hint'}
              </button>
              {aiError && <p className="ai-hint-error">{aiError}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ProgressiveHint
