/**
 * Regression tests for the cross-account data leak.
 *
 * The bug: localStorage is per-browser, not per-account. When account A answered,
 * its result/streak were held in React state and written to shared localStorage.
 * Switching to account B (no page refresh, since the SPA never remounts) left A's
 * data on screen, and sign-in sync uploaded A's localStorage into B's database.
 *
 * These tests drive the real `useAuth` hook (via a captured Supabase auth callback)
 * and the real `App` identity logic, mocking only the API and heavy UI children.
 *
 * Expected: FAIL on the pre-fix App.jsx, PASS on the post-fix App.jsx.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react'

// Hoisted shared handles so the vi.mock factories (which are hoisted) can use them.
const h = vi.hoisted(() => ({
  authCallback: { current: null },
  getSession: vi.fn(),
  signOut: vi.fn(),
  api: {
    getTodayProblem: vi.fn(),
    getProgress: vi.fn(),
    saveProgress: vi.fn(),
    submitAnswer: vi.fn(),
    syncProgress: vi.fn(),
    healthCheck: vi.fn(),
  },
}))

vi.mock('./services/supabase', () => ({
  supabase: {
    auth: {
      onAuthStateChange: (cb) => {
        h.authCallback.current = cb
        return { data: { subscription: { unsubscribe: () => {} } } }
      },
      getSession: h.getSession,
      signOut: h.signOut,
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signInWithOAuth: vi.fn(),
    },
  },
}))

vi.mock('./services/api', () => ({ apiService: h.api }))

// Stub heavy / irrelevant UI so we can assert on coarse state transitions.
vi.mock('better-react-mathjax', () => ({ MathJaxContext: ({ children }) => children }))
vi.mock('@vercel/analytics/react', () => ({ Analytics: () => null }))
vi.mock('./components/ProblemDisplay', () => ({ default: () => <div data-testid="problem" /> }))
vi.mock('./components/ProgressiveHint', () => ({ default: () => null }))
vi.mock('./components/AuthModal', () => ({ default: () => null }))
vi.mock('./components/UserMenu', () => ({ default: () => null }))
vi.mock('./components/StatsPanel', () => ({ default: () => null }))
vi.mock('./components/ResultMessage', () => ({
  default: ({ result }) =>
    result ? <div data-testid="result">{result.is_correct ? 'correct' : 'incorrect'}</div> : null,
}))
vi.mock('./components/AnswerInput', () => ({
  default: ({ onChange, onSubmit }) => (
    <div>
      <button data-testid="type" onClick={() => onChange('x + C')}>type</button>
      <button data-testid="submit" onClick={onSubmit}>submit</button>
    </div>
  ),
}))

import App from './App'

const TODAY = new Date().toLocaleDateString('sv')
const PROBLEM = {
  id: 1,
  date: TODAY,
  problem: '\\int x^2 dx',
  solution: '\\frac{x^3}{3} + C',
  difficulty: 'easy',
  progressive_hints: [],
}
const SESSION_A = { user: { id: 'user-A' }, access_token: 'tok-A' }
const SESSION_B = { user: { id: 'user-B' }, access_token: 'tok-B' }

function resultKeys() {
  const keys = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith('daily-result-')) keys.push(k)
  }
  return keys
}

const signIn = (session) =>
  act(async () => { h.authCallback.current('SIGNED_IN', session) })
const signOut = () =>
  act(async () => { h.authCallback.current('SIGNED_OUT', null) })

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  h.getSession.mockResolvedValue({ data: { session: null } })
  h.signOut.mockResolvedValue({ error: null })
  h.api.getTodayProblem.mockResolvedValue({ success: true, problem: PROBLEM, debug_mode: false })
  h.api.getProgress.mockResolvedValue({ success: true, results: [] })
  h.api.saveProgress.mockResolvedValue({ success: true })
  h.api.syncProgress.mockResolvedValue({ success: true })
})

describe('cross-account data leak', () => {
  it('does not show account A\'s submitted result to account B after switching (no refresh)', async () => {
    h.api.submitAnswer.mockResolvedValue({
      success: true, is_correct: true, message: 'Correct!', user_answer: 'x', correct_answer: 'x',
    })

    render(<App />)
    await screen.findByTestId('problem')
    await signIn(SESSION_A)
    await waitFor(() => expect(screen.getByTestId('submit')).toBeInTheDocument())

    // Account A answers today's problem.
    fireEvent.click(screen.getByTestId('type'))
    // After submitting, the server reflects A's solve (drives the post-fix streak refresh).
    h.api.getProgress.mockResolvedValue({
      success: true, results: [{ date: TODAY, is_correct: true, difficulty: 'easy', problem_id: 1 }],
    })
    await act(async () => { fireEvent.click(screen.getByTestId('submit')) })
    await waitFor(() => expect(screen.getByTestId('result')).toHaveTextContent('correct'))

    // Switch to account B, which has no progress — without any page refresh.
    h.api.getProgress.mockResolvedValue({ success: true, results: [] })
    await signOut()
    await signIn(SESSION_B)

    // B must see a fresh answer prompt, NOT A's result.
    await waitFor(() => expect(screen.getByTestId('submit')).toBeInTheDocument())
    expect(screen.queryByTestId('result')).not.toBeInTheDocument()
  })

  it('restores a logged-in user\'s lock state from the server, not localStorage', async () => {
    // Account A already solved today's problem on the server.
    h.api.getProgress.mockResolvedValue({
      success: true, results: [{ date: TODAY, is_correct: true, difficulty: 'easy', problem_id: 1 }],
    })

    render(<App />)
    await screen.findByTestId('problem')
    await signIn(SESSION_A)

    // The locked "already solved" result must be shown, sourced from the server.
    await waitFor(() => expect(screen.getByTestId('result')).toHaveTextContent('correct'))
    expect(screen.queryByTestId('submit')).not.toBeInTheDocument()
    // And the header streak reflects the server history.
    expect(document.querySelector('.streak-badge .count')?.textContent).toBe('1')
  })

  it('saves a logged-in submission to the server and never to localStorage', async () => {
    h.api.submitAnswer.mockResolvedValue({
      success: true, is_correct: true, message: 'Correct!', user_answer: 'x', correct_answer: 'x',
    })

    render(<App />)
    await screen.findByTestId('problem')
    await signIn(SESSION_A)
    await waitFor(() => expect(screen.getByTestId('submit')).toBeInTheDocument())

    fireEvent.click(screen.getByTestId('type'))
    await act(async () => { fireEvent.click(screen.getByTestId('submit')) })
    await waitFor(() => expect(screen.getByTestId('result')).toBeInTheDocument())

    expect(h.api.saveProgress).toHaveBeenCalledTimes(1)
    expect(resultKeys()).toEqual([]) // no shared localStorage write for logged-in users
  })

  it('migrates anonymous localStorage progress on sign-in, then clears it', async () => {
    // Progress earned while logged out.
    localStorage.setItem(
      'daily-result-2025-01-01',
      JSON.stringify({ is_correct: true, difficulty: 'easy', problem_id: 7 }),
    )

    render(<App />)
    await screen.findByTestId('problem')
    await signIn(SESSION_A)

    await waitFor(() => expect(h.api.syncProgress).toHaveBeenCalledTimes(1))
    expect(h.api.syncProgress).toHaveBeenCalledWith([
      expect.objectContaining({ date: '2025-01-01', problem_id: 7, is_correct: true }),
    ])
    // Migrated data must be cleared so it can't leak into the next account on this browser.
    await waitFor(() => expect(resultKeys()).toEqual([]))
  })
})
