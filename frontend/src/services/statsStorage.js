const RESULT_PREFIX = 'daily-result-'

/**
 * Scans localStorage for all daily result entries.
 * Returns array of { date, is_correct, difficulty, problem_id }
 */
export function getAllResults() {
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
 * Aggregates stats from all stored results.
 */
export function aggregateStats() {
  const results = getAllResults()

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

  // Calculate currentStreak and bestStreak from the sorted results array.
  // A streak is consecutive calendar days with correct answers.
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
 * Given a sorted array of results ({ date, is_correct, ... }),
 * calculate the current streak and best streak.
 *
 * A streak = consecutive calendar days where is_correct === true.
 * "Current streak" counts backwards from today (or yesterday if today has no entry yet).
 * "Best streak" is the longest streak ever achieved.
 *
 * Return { currentStreak: number, bestStreak: number }
 */
function calculateStreaks(results) {

  if (!results.length) {
    return {currentStreak: 0, bestStreak: 0}
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

  return { currentStreak, bestStreak};
}
