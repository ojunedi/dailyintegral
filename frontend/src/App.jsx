import { useState, useEffect } from 'react'
import { MathJaxContext } from 'better-react-mathjax'
import ProblemDisplay from './components/ProblemDisplay'
import AnswerInput from './components/AnswerInput'
import ResultMessage from './components/ResultMessage'
import ProgressiveHint from './components/ProgressiveHint'
import { apiService } from './services/api'

function App() {
  const [problem, setProblem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)
  const [streak, setStreak] = useState(() => {
    const saved = localStorage.getItem('integral-streak')
    return saved ? parseInt(saved, 10) : 0
  })

  useEffect(() => {
    loadProblem()
  }, [])

  const loadProblem = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiService.getTodayProblem()

      if (response.success) {
        setProblem(response.problem)
      } else {
        setError(response.error || 'Failed to load problem')
      }
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!userAnswer.trim()) return

    try {
      setSubmitted(true)
      const response = await apiService.submitAnswer(userAnswer, problem)
      setResult(response)

      // Update streak on correct answer
      if (response.is_correct) {
        const newStreak = streak + 1
        setStreak(newStreak)
        localStorage.setItem('integral-streak', newStreak.toString())
      }
    } catch (err) {
      setResult({ success: false, error: err.message })
    }
  }

  const handleReset = () => {
    setUserAnswer('')
    setSubmitted(false)
    setResult(null)
    loadProblem()
  }

  const mathJaxConfig = {
    loader: { load: ["[tex]/html"] },
    tex: {
      packages: { "[+]": ["html"] },
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["$$", "$$"]],
    },
  }

  if (loading) {
    return (
      <div className="app">
        <div className="container">
          <header className="header">
            <h1>Daily <span className="accent">Integral</span></h1>
            <p className="subtitle">Challenge your calculus skills</p>
          </header>
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Loading today's challenge...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app">
        <div className="container">
          <header className="header">
            <h1>Daily <span className="accent">Integral</span></h1>
            <p className="subtitle">Challenge your calculus skills</p>
          </header>
          <div className="error-state">
            <div className="icon">⚠️</div>
            <p>{error}</p>
            <button onClick={loadProblem} className="button button-primary">
              Try Again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <MathJaxContext config={mathJaxConfig}>
      <div className="app">
        <div className="container">
          <header className="header">
            <h1>Daily <span className="accent">Integral</span></h1>
            <p className="subtitle">Challenge your calculus skills</p>
            {streak > 0 && (
              <div className="streak-badge">
                <span className="flame">🔥</span>
                <span className="count">{streak}</span>
                <span>day streak</span>
              </div>
            )}
          </header>

          {problem && <ProblemDisplay problem={problem} />}

          {!submitted ? (
            <>
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
              <button onClick={handleReset} className="button button-secondary">
                Next Challenge →
              </button>
            </div>
          )}
        </div>
      </div>
    </MathJaxContext>
  )
}

export default App
