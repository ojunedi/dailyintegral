import { useState, useEffect, useRef } from 'react'
import { MathJaxContext } from 'better-react-mathjax'
import ProblemDisplay from './components/ProblemDisplay'
import AnswerInput from './components/AnswerInput'
import ResultMessage from './components/ResultMessage'
import ProgressiveHint from './components/ProgressiveHint'
import AuthModal from './components/AuthModal'
import UserMenu from './components/UserMenu'
import { apiService } from './services/api'
import { useAuth } from './hooks/useAuth'
import { getAllLocalResults } from './services/statsStorage'
import { Analytics } from '@vercel/analytics/react'
import StatsPanel from './components/StatsPanel'

function App() {
  const { user, session, loading: authLoading, signIn, signUp, signInWithGoogle, signOut } = useAuth()
  const [problem, setProblem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)
  const [debugMode, setDebugMode] = useState(false)
  const [dailyLocked, setDailyLocked] = useState(false)
  const [streak, setStreak] = useState(() => {
    const saved = localStorage.getItem('integral-streak')
    return saved ? parseInt(saved, 10) : 0
  })
  const [bestStreak, setBestStreak] = useState(() => {
    const saved = localStorage.getItem('best-streak')
    return saved ? parseInt(saved, 10) : 0
  })
  const [statsOpen, setStatsOpen] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const hasSynced = useRef(false)

  const getTodayKey = () => new Date().toISOString().split('T')[0]

  useEffect(() => {
    loadProblem()
  }, [])

  // Sync localStorage to server on first sign-in
  useEffect(() => {
    if (!session || hasSynced.current) return
    hasSynced.current = true

    const localResults = getAllLocalResults()
    if (localResults.length > 0) {
      const validEntries = localResults.filter(r => r.problem_id != null)
      if (validEntries.length > 0) {
        apiService.syncProgress(validEntries).catch(err =>
          console.error('Failed to sync localStorage to server:', err)
        )
      }
    }
  }, [session])

  const loadProblem = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiService.getTodayProblem()

      if (response.success) {
        setProblem(response.problem)
        setDebugMode(response.debug_mode || false)

        // Check if user already submitted today's daily problem
        if (!response.debug_mode) {
          const savedResult = localStorage.getItem(`daily-result-${getTodayKey()}`)
          if (savedResult) {
            setSubmitted(true)
            setResult(JSON.parse(savedResult))
            setDailyLocked(true)
          }
        }
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

      // In daily mode, lock after submission and persist enriched result
      if (!debugMode) {
        setDailyLocked(true)
        const enrichedResult = {
          ...response,
          difficulty: problem?.difficulty,
          problem_id: problem?.id,
        }
        localStorage.setItem(`daily-result-${getTodayKey()}`, JSON.stringify(enrichedResult))

        // Save to server if logged in (fire-and-forget)
        if (session) {
          apiService.saveProgress({
            date: getTodayKey(),
            problem_id: problem?.id,
            is_correct: response.is_correct,
            difficulty: problem?.difficulty,
          }).catch(err => console.error('Failed to save progress to server:', err))
        }
      }

      // Update streak on correct answer (daily mode only)
      if (response.is_correct && !debugMode) {
        const newStreak = streak + 1
        setStreak(newStreak)
        localStorage.setItem('integral-streak', newStreak.toString())

        if (newStreak > bestStreak) {
          setBestStreak(newStreak)
          localStorage.setItem('best-streak', newStreak.toString())
        }
      }
    } catch (err) {
      setResult({ success: false, error: err.message })
    }
  }

  const handleReset = () => {
    setUserAnswer('')
    setSubmitted(false)
    setResult(null)
    setDailyLocked(false)
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

  if (loading || authLoading) {
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
    <>
      <MathJaxContext config={mathJaxConfig}>
      <div className="app">
        <div className="container">
          <header className="header">
            <h1>Daily <span className="accent">Integral</span></h1>
            <p className="subtitle">Challenge your calculus skills</p>
            <div className="header-badges">
              {debugMode && (
                <div className="debug-badge">
                  DEBUG MODE
                </div>
              )}
              {streak > 0 && (
                <div className="streak-badge">
                  <span className="flame">🔥</span>
                  <span className="count">{streak}</span>
                  <span>day streak</span>
                </div>
              )}
              <button className="stats-toggle-button" onClick={() => setStatsOpen(true)}>
                Stats
              </button>
              <UserMenu
                user={user}
                onSignIn={() => setAuthOpen(true)}
                onSignOut={signOut}
              />
            </div>
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
              {debugMode ? (
                <button onClick={handleReset} className="button button-secondary">
                  Next Challenge →
                </button>
              ) : (
                <div className="daily-lock-message">
                  <p>Come back tomorrow for a new challenge!</p>
                </div>
              )}
            </div>
          )}
        </div>
        <StatsPanel isOpen={statsOpen} onClose={() => setStatsOpen(false)} session={session} />
        <AuthModal
          isOpen={authOpen}
          onClose={() => setAuthOpen(false)}
          onSignIn={signIn}
          onSignUp={signUp}
          onGoogleSignIn={signInWithGoogle}
        />
      </div>
    </MathJaxContext>
    <Analytics />
    </>
  )
}

export default App
