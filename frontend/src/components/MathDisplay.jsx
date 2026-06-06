import { MathJax } from 'better-react-mathjax'

function MathDisplay({ children, inline = false, className = '' }) {
  // `dynamic` makes MathJax re-typeset when `children` changes in place (e.g. the
  // post-submit answer, or a problem update) instead of only on first mount —
  // production builds skip the re-typeset otherwise.
  if (inline) {
    return (
      <MathJax inline dynamic className={className}>
        {`\\(${children}\\)`}
      </MathJax>
    )
  }

  return (
    <MathJax dynamic className={className}>
      {`$$${children}$$`}
    </MathJax>
  )
}

export default MathDisplay