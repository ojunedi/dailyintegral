import { useState } from 'react'

function AuthModal({ isOpen, onClose, onSignIn, onSignUp, onGoogleSignIn }) {
  const [mode, setMode] = useState('signin') // 'signin' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [signUpSuccess, setSignUpSuccess] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (mode === 'signin') {
        await onSignIn(email, password)
        onClose()
      } else {
        await onSignUp(email, password)
        setSignUpSuccess(true)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleClick = async () => {
    setError(null)
    try {
      await onGoogleSignIn()
    } catch (err) {
      setError(err.message)
    }
  }

  const switchMode = () => {
    setMode(mode === 'signin' ? 'signup' : 'signin')
    setError(null)
    setSignUpSuccess(false)
  }

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-close-btn" onClick={onClose} aria-label="Close">
          &#x2715;
        </button>

        <h2 className="auth-title">
          {mode === 'signin' ? 'Sign In' : 'Create Account'}
        </h2>
        <p className="auth-subtitle">
          {mode === 'signin'
            ? 'Sync your progress across devices'
            : 'Track your streak everywhere'}
        </p>

        {signUpSuccess ? (
          <div className="auth-success">
            <p>Check your email for a confirmation link!</p>
            <button className="auth-btn auth-btn-primary" onClick={() => { setMode('signin'); setSignUpSuccess(false) }}>
              Back to Sign In
            </button>
          </div>
        ) : (
          <>
            <button className="auth-btn auth-btn-google" onClick={handleGoogleClick}>
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
                <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.26c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
                <path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </button>

            <div className="auth-divider">
              <span>or</span>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="auth-input"
                required
                autoComplete="email"
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="auth-input"
                required
                minLength={6}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              />

              {error && <p className="auth-error">{error}</p>}

              <button
                type="submit"
                className="auth-btn auth-btn-primary"
                disabled={loading}
              >
                {loading ? 'Loading...' : mode === 'signin' ? 'Sign In' : 'Sign Up'}
              </button>
            </form>

            <p className="auth-switch">
              {mode === 'signin' ? "Don't have an account?" : 'Already have an account?'}{' '}
              <button onClick={switchMode} className="auth-switch-btn">
                {mode === 'signin' ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  )
}

export default AuthModal
