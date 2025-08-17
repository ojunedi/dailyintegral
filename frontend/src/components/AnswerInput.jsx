import { useState } from 'react';

function AnswerInput({ onSubmit, loading, disabled }) {
  const [answer, setAnswer] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (answer.trim() && !loading) {
      onSubmit(answer.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="space-y-4">
        <div>
          <label htmlFor="answer" className="block text-sm font-medium text-gray-700 mb-2">
            Your Answer (LaTeX format):
          </label>
          <input
            type="text"
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={disabled || loading}
            placeholder="e.g., \\frac{x^3}{3} + C"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed font-mono text-lg"
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter your answer in LaTeX format. Use \\frac{}{} for fractions, x^{} for exponents.
          </p>
        </div>
        
        <button
          type="submit"
          disabled={!answer.trim() || loading || disabled}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Checking...
            </span>
          ) : (
            'Submit Answer'
          )}
        </button>
      </div>
    </form>
  );
}

export default AnswerInput;