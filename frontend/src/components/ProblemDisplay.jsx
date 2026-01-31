import MathDisplay from './MathDisplay'

function ProblemDisplay({ problem }) {
  const difficultyClass = problem.difficulty?.toLowerCase() || 'easy'

  return (
    <div className="problem-display">
      <h2>Today's Problem</h2>
      <div className="problem-content">
        <p>Evaluate the integral:</p>
        <div className="problem-equation">
          <MathDisplay>{problem.latex_problem || problem.problem}</MathDisplay>
        </div>
        {problem.difficulty && (
          <span className={`difficulty ${difficultyClass}`}>
            {problem.difficulty}
          </span>
        )}
      </div>
    </div>
  )
}

export default ProblemDisplay
