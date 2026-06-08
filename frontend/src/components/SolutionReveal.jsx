import { useState } from 'react'
import MathDisplay from './MathDisplay'

/**
 * SolutionReveal - shows the full worked solution to a problem.
 *
 * Self-contained: owns its own open/closed state so App.jsx needs only a single
 * render line. Behavior depends on whether the problem has been answered:
 *   - unsolved          → a "Give up & reveal solution" button (reveal-only, no lock)
 *   - solved + correct  → auto-expanded so the user can compare their work
 *   - solved + wrong    → collapsed behind a "Show solution" toggle
 *
 * The solution field is stored as pure LaTeX, so it renders via MathDisplay ($$...$$),
 * mirroring how the problem statement is rendered. Styled distinct from the amber
 * hints (purple/green) so it clearly reads as "the solution".
 */
function SolutionReveal({ solution, solved, correct }) {
  const [revealed, setRevealed] = useState(false)

  if (!solution) return null

  // Auto-reveal when the user solved it correctly; otherwise it's behind a button.
  const isOpen = revealed || (solved && correct)

  if (isOpen) {
    return (
      <div className="solution-reveal open">
        <div className="solution-header">
          <span className="icon">✅</span>
          <span>Worked Solution</span>
        </div>
        <div className="solution-content">
          <MathDisplay>{solution}</MathDisplay>
        </div>
      </div>
    )
  }

  const label = solved ? 'Show solution' : 'Give up & reveal solution'
  const icon = solved ? '📖' : '🏳️'

  return (
    <div className="solution-reveal">
      <button
        type="button"
        className="solution-toggle"
        onClick={() => setRevealed(true)}
      >
        <span className="icon">{icon}</span>
        <span>{label}</span>
      </button>
    </div>
  )
}

export default SolutionReveal
