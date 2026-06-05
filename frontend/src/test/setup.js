import '@testing-library/jest-dom'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Reset DOM and localStorage between tests so state can't leak across cases.
afterEach(() => {
  cleanup()
  localStorage.clear()
})
