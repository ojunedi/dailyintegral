import MathInput from './MathInput'

function AnswerInput({ value, onChange, onSubmit, disabled }) {
  return (
    <div className="answer-input">
      <label htmlFor="answer">Your answer:</label>
      <MathInput
        value={value}
        onChange={onChange}
        onSubmit={onSubmit}
        placeholder="\text{Enter your answer here}"
      />
      <button
        onClick={onSubmit}
        disabled={disabled}
        className="button button-primary"
      >
        Submit Answer
      </button>
    </div>
  )
}

export default AnswerInput
