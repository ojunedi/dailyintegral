import { useState, useEffect } from 'react'
import { getResults, computeStats, aggregateStats } from '../services/statsStorage'
import CalendarGrid from './CalendarGrid'

function StatsPanel({ isOpen, onClose, session }) {
  const [stats, setStats] = useState(null)
  const now = new Date()
  const [calMonth, setCalMonth] = useState(now.getMonth())
  const [calYear, setCalYear] = useState(now.getFullYear())

  useEffect(() => {
    if (!isOpen) return
    let cancelled = false

    if (session) {
      // Async fetch from server
      getResults(session).then(results => {
        if (!cancelled) setStats(computeStats(results))
      })
    } else {
      setStats(aggregateStats())
    }

    return () => { cancelled = true }
  }, [isOpen, session])

  if (!isOpen) return null

  const handlePrevMonth = () => {
    if (calMonth === 0) {
      setCalMonth(11)
      setCalYear(y => y - 1)
    } else {
      setCalMonth(m => m - 1)
    }
  }

  const handleNextMonth = () => {
    if (calMonth === 11) {
      setCalMonth(0)
      setCalYear(y => y + 1)
    } else {
      setCalMonth(m => m + 1)
    }
  }

  const difficultyBar = (label, data, colorClass) => {
    const pct = data.attempted > 0 ? Math.round((data.correct / data.attempted) * 100) : 0
    return (
      <div className="diff-row">
        <span className="diff-label">{label}</span>
        <div className="diff-bar-track">
          <div
            className={`diff-bar-fill ${colorClass}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="diff-stat">{data.correct}/{data.attempted}</span>
      </div>
    )
  }

  return (
    <div className="stats-panel-overlay" onClick={onClose}>
      <div className="stats-panel" onClick={e => e.stopPropagation()}>
        <button className="stats-close-btn" onClick={onClose} aria-label="Close stats">
          &#x2715;
        </button>

        <h2 className="stats-title">Your Stats</h2>

        {stats && (
          <>
            <div className="stats-grid">
              <div className="stat-tile">
                <span className="stat-value">{stats.totalAttempted}</span>
                <span className="stat-label">Attempted</span>
              </div>
              <div className="stat-tile">
                <span className="stat-value">{stats.accuracyRate}%</span>
                <span className="stat-label">Accuracy</span>
              </div>
              <div className="stat-tile">
                <span className="stat-value">{stats.currentStreak}</span>
                <span className="stat-label">Current Streak</span>
              </div>
              <div className="stat-tile">
                <span className="stat-value">{stats.bestStreak}</span>
                <span className="stat-label">Best Streak</span>
              </div>
            </div>

            <div className="difficulty-breakdown">
              <h3 className="diff-heading">By Difficulty</h3>
              {difficultyBar('Easy', stats.byDifficulty.easy, 'diff-bar-easy')}
              {difficultyBar('Medium', stats.byDifficulty.medium, 'diff-bar-medium')}
              {difficultyBar('Hard', stats.byDifficulty.hard, 'diff-bar-hard')}
            </div>

            <CalendarGrid
              resultsByDate={stats.resultsByDate}
              year={calYear}
              month={calMonth}
              onPrevMonth={handlePrevMonth}
              onNextMonth={handleNextMonth}
            />
          </>
        )}
      </div>
    </div>
  )
}

export default StatsPanel
