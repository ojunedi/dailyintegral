import { useState } from 'react'

// Wordle-style shareable summary of today's result.
function buildShareText({ id, correct, streak, difficulty, hintsUsed }) {
  const hintLine =
    hintsUsed > 0 ? `💡 ${hintsUsed} hint${hintsUsed === 1 ? '' : 's'} used` : '🧠 No hints'
  const lines = [
    `Daily Integral #${id} ∫`,
    `${correct ? '✅ Solved' : '❌ Missed'}${difficulty ? ` · ${difficulty}` : ''}`,
    hintLine,
  ]
  if (streak > 0) lines.push(`🔥 ${streak} day streak`)
  lines.push(window.location.origin)
  return lines.join('\n')
}

export default function ShareCard({ id, correct, streak, difficulty, hintsUsed = 0 }) {
  const [copied, setCopied] = useState(false)
  if (id == null) return null

  const text = buildShareText({ id, correct, streak, difficulty, hintsUsed })

  const share = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ text })
        return
      } catch {
        /* user dismissed — fall through to copy */
      }
    }
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <button className="share-button" onClick={share}>
      {copied ? '✓ Copied!' : '🔗 Share result'}
    </button>
  )
}
