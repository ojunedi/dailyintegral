import { useEffect, useState } from 'react'
import MathDisplay from './MathDisplay'

function Particles() {
  const [particles, setParticles] = useState([])

  useEffect(() => {
    const colors = ['#39ff14', '#00fff5', '#ff2e63', '#ffa500', '#bf40ff']
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.5,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: Math.random() * 8 + 6,
    }))
    setParticles(newParticles)

    const timer = setTimeout(() => setParticles([]), 3000)
    return () => clearTimeout(timer)
  }, [])

  if (particles.length === 0) return null

  return (
    <div className="particles">
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: `${p.left}%`,
            backgroundColor: p.color,
            width: p.size,
            height: p.size,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  )
}

function ResultMessage({ result }) {
  if (!result) return null

  if (!result.success) {
    return (
      <div className="result-message error">
        <h3 className="result-title">⚠️ Error</h3>
        <p>{result.error || 'Something went wrong'}</p>
      </div>
    )
  }

  const isCorrect = result.is_correct

  return (
    <>
      {isCorrect && <Particles />}
      <div className={`result-message ${isCorrect ? 'success' : 'incorrect'}`}>
        <h3 className="result-title">
          {isCorrect ? '🎉 Correct!' : '❌ Not quite right'}
        </h3>
        <p>{result.message}</p>

        {result.user_answer && (
          <div className="answer-display">
            <p style={{ marginBottom: '4px', opacity: 0.7, fontSize: '0.85rem' }}>
              Your answer:
            </p>
            <MathDisplay>{result.user_answer}</MathDisplay>
          </div>
        )}

        {!isCorrect && result.correct_answer && (
          <div className="answer-display">
            <p style={{ marginBottom: '4px', opacity: 0.7, fontSize: '0.85rem' }}>
              Correct answer:
            </p>
            <MathDisplay>{result.correct_answer}</MathDisplay>
          </div>
        )}
      </div>
    </>
  )
}

export default ResultMessage
