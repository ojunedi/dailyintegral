import { useEffect, useRef } from 'react'
import 'mathlive'

function MathInput({ value, onChange, onSubmit, disabled, placeholder }) {
  const fieldRef = useRef(null)

  // Initialize listeners once
  useEffect(() => {
    const el = fieldRef.current
    if (!el) return

    // Seed initial value if provided
    if (typeof value === 'string' && value !== '') {
      try { el.value = value } catch (e) { /* noop */ }
    }

    const handleInput = (e) => {
      const latex = e?.target?.value ?? ''
      if (onChange) onChange(latex)
    }

    const handleKeyDown = (e) => {
      if ((e.key === 'Enter' || e.key === 'Return') && !disabled) {
        e.preventDefault()
        if (onSubmit) onSubmit()
      }
    }

    el.addEventListener('input', handleInput)
    el.addEventListener('keydown', handleKeyDown)
    return () => {
      el.removeEventListener('input', handleInput)
      el.removeEventListener('keydown', handleKeyDown)
    }
  }, [onChange, onSubmit, disabled])

  // Keep external value in sync if it changes
  useEffect(() => {
    const el = fieldRef.current
    if (!el) return
    if (typeof value === 'string' && el.value !== value) {
      try { el.value = value } catch (e) { /* noop */ }
    }
  }, [value])

  return (
    <div className="math-input-container">
      <math-field
        ref={fieldRef}
        className={disabled ? 'disabled' : ''}
        placeholder={placeholder || 'Enter math here'}
        style={{ width: '100%' }}
      />
    </div>
  )
}

export default MathInput
