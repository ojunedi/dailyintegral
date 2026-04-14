import { useState, useEffect, useRef } from 'react'

function UserMenu({ user, onSignIn, onSignOut }) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open])

  if (!user) {
    return (
      <button className="um-signin-pill" onClick={onSignIn}>
        Sign In
      </button>
    )
  }

  const initial = (user.email?.[0] || '?').toUpperCase()
  const displayName = user.user_metadata?.full_name || user.email
  const email = user.email

  return (
    <div className="um-container" ref={menuRef}>
      <button
        className="um-avatar"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-haspopup="true"
        title={email}
      >
        <span className="um-avatar-letter">{initial}</span>
        <div className="um-avatar-ring" />
      </button>

      {open && (
        <div className="um-dropdown">
          <div className="um-dropdown-arrow" />

          <div className="um-user-info">
            <div className="um-user-name">{displayName}</div>
            {displayName !== email && (
              <div className="um-user-email">{email}</div>
            )}
          </div>

          <div className="um-divider" />

          <button
            className="um-signout-btn"
            onClick={() => {
              setOpen(false)
              onSignOut()
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign Out
          </button>
        </div>
      )}
    </div>
  )
}

export default UserMenu
