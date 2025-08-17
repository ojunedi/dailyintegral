function ProblemDisplay({ problem, loading, error }) {
  if (loading) {
    return (
      <div className="text-center p-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">Loading today's problem...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-700">Error loading problem: {error}</p>
      </div>
    );
  }

  if (!problem) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-600">No problem available</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
      <div className="text-center">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          Today's Integral Problem
        </h2>
        
        {/* Problem display - for now showing LaTeX as text, will add MathJax later */}
        <div className="text-3xl font-mono bg-gray-50 p-6 rounded-lg border mb-6">
          {problem.problem}
        </div>
        
        <div className="text-sm text-gray-600 mb-2">
          <span className="font-medium">Difficulty:</span> 
          <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
            problem.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
            problem.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            {problem.difficulty}
          </span>
        </div>
        
        {problem.hint && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-medium text-blue-800 mb-1">Hint:</p>
            <p className="text-sm text-blue-700 font-mono">{problem.hint}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProblemDisplay;