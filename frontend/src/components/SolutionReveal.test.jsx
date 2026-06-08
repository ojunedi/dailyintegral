import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

// MathJax is heavy and DOM-only; render its children as plain text so we can
// assert on the rendered LaTeX.
vi.mock('better-react-mathjax', () => ({
  MathJax: ({ children }) => <span>{children}</span>,
}))

import SolutionReveal from './SolutionReveal'

const SOLUTION = '\\frac{x^3}{3} + C'

describe('SolutionReveal', () => {
  it('renders nothing when there is no solution', () => {
    const { container } = render(<SolutionReveal solution={null} solved={false} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('hides the solution behind a "give up" button while unsolved', () => {
    render(<SolutionReveal solution={SOLUTION} solved={false} />)
    expect(screen.getByRole('button', { name: /give up/i })).toBeInTheDocument()
    expect(screen.queryByText(/Worked Solution/i)).not.toBeInTheDocument()
  })

  it('reveals the worked solution when the give-up button is clicked', () => {
    render(<SolutionReveal solution={SOLUTION} solved={false} />)
    fireEvent.click(screen.getByRole('button', { name: /give up/i }))
    expect(screen.getByText(/Worked Solution/i)).toBeInTheDocument()
    expect(screen.getByText(new RegExp('x\\^3', 'i'))).toBeInTheDocument()
  })

  it('auto-shows the worked solution when answered correctly', () => {
    render(<SolutionReveal solution={SOLUTION} solved={true} correct={true} />)
    expect(screen.getByText(/Worked Solution/i)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('keeps the solution behind a "show solution" toggle when answered incorrectly', () => {
    render(<SolutionReveal solution={SOLUTION} solved={true} correct={false} />)
    const button = screen.getByRole('button', { name: /show solution/i })
    expect(button).toBeInTheDocument()
    expect(screen.queryByText(/Worked Solution/i)).not.toBeInTheDocument()
    fireEvent.click(button)
    expect(screen.getByText(/Worked Solution/i)).toBeInTheDocument()
  })
})
