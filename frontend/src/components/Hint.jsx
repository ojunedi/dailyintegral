import { useState } from 'react'
import MathDisplay from './MathDisplay'

function Hint({ hint }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!hint) {
    return null
  }

  // TODO(human): Add hint interaction logic
  // Consider adding analytics tracking or progressive hint revealing

  return (
    <div className="hint-container mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`hint-toggle w-full text-left p-3 rounded-lg border-2 transition-all duration-200 ${
          isOpen 
            ? 'border-yellow-400 bg-yellow-50' 
            : 'border-gray-300 bg-gray-50 hover:border-yellow-300 hover:bg-yellow-25'
        }`}
        type="button"
      >
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-700 flex items-center">
            💡 Need a hint?
          </span>
          <span className={`transform transition-transform duration-200 text-gray-500 ${
            isOpen ? 'rotate-180' : 'rotate-0'
          }`}>
            ▼
          </span>
        </div>
      </button>
      
      {isOpen && (
        <div className="hint-content mt-2 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg">
          <div className="text-gray-700">
            <MathDisplay>{hint}</MathDisplay>
          </div>
        </div>
      )}
    </div>
  )
}

export default Hint