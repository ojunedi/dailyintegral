import { MathJax } from 'better-react-mathjax'

/**
 * HintDisplay - Renders text with optional inline math
 *
 * Plain text renders normally. Wrap math in $...$ for inline rendering.
 * Example: "Use the power rule: $\int x^n dx = \frac{x^{n+1}}{n+1}$"
 *
 * If the entire hint is a LaTeX expression (starts with \),
 * it renders as display math.
 */
function HintDisplay({ children }) {
  if (!children) return null

  const text = String(children)

  // Check if it's a pure LaTeX expression (starts with backslash)
  const isPureLatex = text.trim().startsWith('\\')

  if (isPureLatex) {
    // Render as display math
    return (
      <MathJax>
        {`$$${text}$$`}
      </MathJax>
    )
  }

  // Check if it contains inline math delimiters $...$
  const hasInlineMath = /\$[^$]+\$/.test(text)

  if (hasInlineMath) {
    // Split by $...$ and render mixed content
    // MathJax will process \(...\) as inline math
    const processed = text.replace(/\$([^$]+)\$/g, '\\($1\\)')
    return (
      <MathJax inline>
        {processed}
      </MathJax>
    )
  }

  // Plain text - just render as-is (Unicode math symbols will show fine)
  return <span className="hint-text">{text}</span>
}

export default HintDisplay
