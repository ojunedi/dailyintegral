import { apiService } from './api'

const RESULT_PREFIX = 'daily-result-'

/**
 * Scans localStorage for all daily result entries.
 * Returns array of { date, is_correct, difficulty, problem_id }
 */
export function getAllLocalResults() {
  const results = []
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key.startsWith(RESULT_PREFIX)) {
      const date = key.slice(RESULT_PREFIX.length)
      try {
        const data = JSON.parse(localStorage.getItem(key))
        results.push({
          date,
          is_correct: data.is_correct ?? false,
          difficulty: data.difficulty ?? 'unknown',
          problem_id: data.problem_id ?? null,
        })
      } catch {
        // skip corrupted entries
      }
    }
  }
  return results.sort((a, b) => a.date.localeCompare(b.date))
}

/**
 * Fetch results from the server for authenticated users.
 */
async function getServerResults() {
  const response = await apiService.getProgress()
  if (!response.success) return []
  return response.results.map(r => ({
    date: r.date,
    is_correct: r.is_correct,
    difficulty: r.difficulty,
    problem_id: r.problem_id,
  }))
}

/**
 * Get results from the appropriate source based on auth state.
 */
export async function getResults(session) {
  if (session) {
    try {
      return await getServerResults()
    } catch {
      // Fall back to localStorage on network error
      return getAllLocalResults()
    }
  }
  return getAllLocalResults()
}

/**
 * Aggregates stats from a results array.
 */
export function computeStats(results) {
  const totalAttempted = results.length
  const totalCorrect = results.filter(r => r.is_correct).length
  const accuracyRate = totalAttempted > 0 ? Math.round((totalCorrect / totalAttempted) * 100) : 0

  // Difficulty breakdown
  const byDifficulty = { easy: { attempted: 0, correct: 0 }, medium: { attempted: 0, correct: 0 }, hard: { attempted: 0, correct: 0 } }
  for (const r of results) {
    const key = r.difficulty?.toLowerCase()
    if (byDifficulty[key]) {
      byDifficulty[key].attempted++
      if (r.is_correct) byDifficulty[key].correct++
    }
  }

  // Date lookup map for calendar
  const resultsByDate = {}
  for (const r of results) {
    resultsByDate[r.date] = { is_correct: r.is_correct, difficulty: r.difficulty }
  }

  const { currentStreak, bestStreak } = calculateStreaks(results)

  return {
    totalAttempted,
    totalCorrect,
    accuracyRate,
    currentStreak,
    bestStreak,
    byDifficulty,
    resultsByDate,
  }
}

/**
 * Synchronous aggregation from localStorage only (backwards-compatible).
 */
export function aggregateStats() {
  return computeStats(getAllLocalResults())
}

function calculateStreaks(results) {
  if (!results.length) {
    return { currentStreak: 0, bestStreak: 0 }
  }

  let bestStreak = results[0]?.is_correct ? 1 : 0
  let currentStreak = 1;
  let prev = results[0];
  for (const r of results.slice(1)) {
    let date = r.date;
    let is_correct = r.is_correct;
    if ((new Date(date) - new Date(prev.date)) / 86400000 === 1 && is_correct && prev.is_correct) {
      currentStreak += 1
    } else {
      currentStreak = is_correct ? 1 : 0;
    }
    bestStreak = Math.max(bestStreak, currentStreak)
    prev = r;
  }
  const today = new Date().toISOString().split('T')[0]
  const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
  if (prev.date !== today && prev.date !== yesterday) {
    currentStreak = 0;
  }

  return { currentStreak, bestStreak }
}
