import { useState, useEffect } from 'react'
import ProblemDisplay from './ProblemDisplay'
import AnswerInput from './AnswerInput'
import ResultMessage from './ResultMessage'
import ProgressiveHint from './ProgressiveHint'
import { apiService } from '../services/api'

// Self-contained practice flow. Keeps its own local state so it can never touch
// the daily streak / progress paths in App.jsx — practice attempts are never
// persisted (no calls to saveProgress / localStorage daily keys).
function PracticeMode() {
  const [problem, setProblem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)

  const loadProblem = async () => {
    try {
      setLoading(true)
      setError(null)
      setUserAnswer('')
      setSubmitted(false)
      setResult(null)
      const response = await apiService.getPracticeProblem()
      if (response.success) {
        setProblem(response.problem)
      } else {
        setError(response.error || 'Failed to load practice problem')
      }
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProblem()
  }, [])

  const handleSubmit = async () => {
    if (!userAnswer.trim()) return
    try {
      const response = await apiService.submitAnswer(userAnswer, problem)
      setResult(response)
      // Only a genuinely graded response locks the attempt; a parse/processing
      // error (success: false) leaves the input open for a retry.
      if (!response.success) return
      setSubmitted(true)
    } catch (err) {
      setResult({ success: false, error: err.message })
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Loading a practice problem...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-state">
        <div className="icon">⚠️</div>
        <p>{error}</p>
        <button onClick={loadProblem} className="button button-primary">
          Try Again
        </button>
      </div>
    )
  }

  return (
    <>
      {problem && <ProblemDisplay problem={problem} />}

      {!submitted ? (
        <>
          {result && !result.success && <ResultMessage result={result} />}
          <ProgressiveHint hints={problem?.progressive_hints} />
          <AnswerInput
            value={userAnswer}
            onChange={setUserAnswer}
            onSubmit={handleSubmit}
            disabled={!userAnswer.trim()}
          />
        </>
      ) : (
        <div>
          <ResultMessage result={result} />
          <button onClick={loadProblem} className="button button-secondary">
            Next problem →
          </button>
        </div>
      )}
    </>
  )
}

export default PracticeMode
