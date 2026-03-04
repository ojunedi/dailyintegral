import { MathJax } from 'better-react-mathjax'

function MathDisplay({ children, inline = false, className = '' }) {
  if (inline) {
    return (
      <MathJax inline className={className}>
        {`\\(${children}\\)`}
      </MathJax>
    )
  }

  return (
    <MathJax className={className}>
      {`$$${children}$$`}
    </MathJax>
  )
}

export default MathDisplay