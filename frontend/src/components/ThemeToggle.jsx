import { useState, useEffect } from 'react'

// Read the theme already applied by the inline script in index.html so the
// button starts in sync (no flash, no mismatch). Falls back to stored value,
// then defaults to dark.
function getInitialTheme() {
  const applied = document.documentElement.getAttribute('data-theme')
  if (applied) return applied
  try {
    const stored = localStorage.getItem('theme')
    if (stored) return stored
  } catch { /* localStorage unavailable */ }
  return 'dark'
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(getInitialTheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('theme', theme) } catch { /* ignore */ }
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) meta.setAttribute('content', theme === 'light' ? '#f4f6fa' : '#0d0d1a')
  }, [theme])

  const next = theme === 'light' ? 'dark' : 'light'

  return (
    <button
      className="theme-toggle"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
    >
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  )
}
