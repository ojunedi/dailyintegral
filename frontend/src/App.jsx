import { useState, useEffect, useRef } from 'react'
import { MathJaxContext } from 'better-react-mathjax'
import ProblemDisplay from './components/ProblemDisplay'
import AnswerInput from './components/AnswerInput'
import ResultMessage from './components/ResultMessage'
import ProgressiveHint from './components/ProgressiveHint'
import ShareCard from './components/ShareCard'
import SolutionReveal from './components/SolutionReveal'
import AuthModal from './components/AuthModal'
import UserMenu from './components/UserMenu'
import { apiService } from './services/api'
import { useAuth } from './hooks/useAuth'
import { getAllLocalResults, aggregateStats, computeStats, clearLocalResults } from './services/statsStorage'
import { Analytics } from '@vercel/analytics/react'
import StatsPanel from './components/StatsPanel'
import PracticeMode from './components/PracticeMode'

function App() {
  const { user, session, loading: authLoading, signIn, signUp, signInWithGoogle, signOut } = useAuth()
  const [problem, setProblem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userAnswer, setUserAnswer] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState(null)
  const [debugMode, setDebugMode] = useState(false)
  // Streak/result are derived per-identity in the identity effect below, never
  // initialized from shared localStorage (which would leak across accounts).
  const [streak, setStreak] = useState(0)
  const [bestStreak, setBestStreak] = useState(0)
  const [hintsUsed, setHintsUsed] = useState(0)
  const [statsOpen, setStatsOpen] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  // Practice mode is an independent UI mode; it never records daily progress.
  const [practiceMode, setPracticeMode] = useState(false)
  const hasSynced = useRef(false)

  // Use local date (YYYY-MM-DD) so the key doesn't flip at 8pm for UTC-4 users
  const getTodayKey = () => new Date().toLocaleDateString('sv')

  useEffect(() => {
    loadProblem()
  }, [])

  // On first sign-in, migrate anonymous localStorage progress into the account,
  // then clear it so it can't leak into a different account on this browser.
  useEffect(() => {
    if (!session) {
      // Signed out — allow the next sign-in to migrate its own anonymous progress.
      hasSynced.current = false
      return
    }
    if (hasSynced.current) return
    hasSynced.current = true

    const validEntries = getAllLocalResults().filter(r => r.problem_id != null)
    if (validEntries.length > 0) {
      apiService.syncProgress(validEntries)
        .then(() => clearLocalResults())
        .catch(err =>
          // Keep the data on failure so it can retry on the next sign-in.
          console.error('Failed to sync localStorage to server:', err)
        )
    } else {
      // Nothing to migrate — clear any leftover anonymous results anyway.
      clearLocalResults()
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
      } else {
        setError(response.error || 'Failed to load problem')
      }
    } catch (err) {
      setError(err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  // Recompute streak from the server (logged-in source of truth).
  const refreshStreakFromServer = async () => {
    try {
      const resp = await apiService.getProgress()
      const results = resp.success ? resp.results : []
      const stats = computeStats(results)
      setStreak(stats.currentStreak)
      setBestStreak(stats.bestStreak)
    } catch (err) {
      console.error('Failed to refresh streak from server:', err)
    }
  }

  // Identity effect: once auth settles, reset any state from a previous identity and
  // re-derive today's lock/result + streak for the CURRENT identity. This runs on
  // login/logout (the SPA never remounts), which is what prevents account A's data
  // from lingering in memory when account B signs in without a page refresh.
  useEffect(() => {
    if (authLoading || !problem || debugMode) return
    let cancelled = false

    // Clear previous identity's in-memory state.
    setSubmitted(false)
    setResult(null)
    setUserAnswer('')
    setStreak(0)
    setBestStreak(0)
    setHintsUsed(0)

    const todayKey = getTodayKey()

    const derive = async () => {
      if (session) {
        // Logged in: the server is the single source of truth — never read localStorage.
        try {
          const resp = await apiService.getProgress()
          if (cancelled) return
          const results = resp.success ? resp.results : []

          const todayEntry = results.find(r => r.date === todayKey)
          if (todayEntry) {
            setSubmitted(true)
            setResult({
              success: true,
              is_correct: todayEntry.is_correct,
              message: todayEntry.is_correct
                ? "You solved today's problem!"
                : "You already attempted today's problem.",
              correct_answer: problem.solution,
            })
          }

          const stats = computeStats(results)
          setStreak(stats.currentStreak)
          setBestStreak(stats.bestStreak)
        } catch (err) {
          console.error('Failed to load progress from server:', err)
        }
      } else {
        // Anonymous: localStorage (single user per browser).
        const savedResult = localStorage.getItem(`daily-result-${todayKey}`)
        if (savedResult) {
          try {
            const parsed = JSON.parse(savedResult)
            if (parsed.problem_id === problem.id) {
              setSubmitted(true)
              setResult(parsed)
            } else {
              localStorage.removeItem(`daily-result-${todayKey}`)
            }
          } catch {
            localStorage.removeItem(`daily-result-${todayKey}`)
          }
        }
        const stats = aggregateStats()
        setStreak(stats.currentStreak)
        setBestStreak(stats.bestStreak)
      }
    }

    derive()
    return () => { cancelled = true }
  }, [session, authLoading, problem, debugMode])

  const handleSubmit = async () => {
    if (!userAnswer.trim()) return

    try {
      const response = await apiService.submitAnswer(userAnswer, problem)
      setResult(response)

      // A malformed-LaTeX / processing error comes back as a response that was never
      // actually graded (e.g. { success: false, error: '...' }). In daily mode we must NOT
      // consume the user's single attempt for these — leave the input visible, lock nothing,
      // and let them fix their answer and resubmit.
      if (!response.success) return

      // Past this point the answer was genuinely graded — commit it as the daily attempt.
      setSubmitted(true)

      // Persist the daily attempt to the appropriate per-identity store.
      if (!debugMode) {
        if (session) {
          // Logged in: server is the source of truth. Save, then recompute streak from it.
          try {
            await apiService.saveProgress({
              date: getTodayKey(),
              problem_id: problem?.id,
              is_correct: response.is_correct,
              difficulty: problem?.difficulty,
            })
          } catch (err) {
            console.error('Failed to save progress to server:', err)
          }
          await refreshStreakFromServer()
        } else {
          // Anonymous: localStorage.
          const enrichedResult = {
            ...response,
            difficulty: problem?.difficulty,
            problem_id: problem?.id,
          }
          localStorage.setItem(`daily-result-${getTodayKey()}`, JSON.stringify(enrichedResult))
          const { currentStreak, bestStreak: newBest } = aggregateStats()
          setStreak(currentStreak)
          setBestStreak(newBest)
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
    setHintsUsed(0)
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
              <button
                className="stats-toggle-button"
                onClick={() => setPracticeMode((p) => !p)}
              >
                {practiceMode ? 'Daily' : 'Practice'}
              </button>
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

          {practiceMode ? (
            <PracticeMode />
          ) : (
            <>
              {problem && <ProblemDisplay problem={problem} />}

              {!submitted ? (
                <>
                  {result && !result.success && <ResultMessage result={result} />}
                  <ProgressiveHint hints={problem?.progressive_hints} onReveal={(n) => setHintsUsed((h) => Math.max(h, n))} />
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
                  <ShareCard
                    id={problem?.id}
                    correct={result?.is_correct}
                    streak={streak}
                    difficulty={problem?.difficulty}
                    hintsUsed={hintsUsed}
                  />
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

              {problem && (
                <SolutionReveal
                  key={problem.id}
                  solution={problem.latex_solution || problem.solution}
                  solved={submitted}
                  correct={result?.is_correct}
                />
              )}
            </>
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
