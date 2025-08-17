import { useState, useEffect } from 'react'
import Header from './components/Header'
import ProblemDisplay from './components/ProblemDisplay'
import AnswerInput from './components/AnswerInput'
import ResultMessage from './components/ResultMessage'
import { apiService } from './services/api'

function App() {
  const [problem, setProblem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)

  // Load today's problem on component mount
  useEffect(() => {
    loadProblem()
  }, [])

  const loadProblem = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiService.getTodayProblem()
      
      if (response.success) {
        setProblem(response.problem)
      } else {
        setError(response.error || 'Failed to load problem')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitAnswer = async (answer) => {
    try {
      setSubmitting(true)
      setResult(null)
      
      const response = await apiService.submitAnswer(answer)
      setResult(response)
    } catch (err) {
      setResult({
        success: false,
        error: err.message
      })
    } finally {
      setSubmitting(false)
    }
  }

  const handleTryAgain = () => {
    setResult(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-4xl mx-auto p-6 space-y-6">
        <ProblemDisplay 
          problem={problem} 
          loading={loading} 
          error={error} 
        />
        
        {result && (
          <ResultMessage 
            result={result} 
            onTryAgain={handleTryAgain} 
          />
        )}
        
        {problem && !loading && (
          <AnswerInput 
            onSubmit={handleSubmitAnswer}
            loading={submitting}
            disabled={result?.success && result?.is_correct}
          />
        )}
        
        {error && (
          <div className="text-center">
            <button
              onClick={loadProblem}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Try loading again
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
