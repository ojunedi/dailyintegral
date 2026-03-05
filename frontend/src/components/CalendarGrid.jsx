function CalendarGrid({ resultsByDate, year, month, onPrevMonth, onNextMonth }) {
  const DAY_LABELS = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]

  // First day of month and total days
  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const monthName = new Date(year, month).toLocaleString('default', { month: 'long' })

  // Build day cells with leading blanks for alignment
  const blanks = Array.from({ length: firstDay }, (_, i) => (
    <div key={`blank-${i}`} className="cal-day cal-day-empty" />
  ))

  const days = Array.from({ length: daysInMonth }, (_, i) => {
    const day = i + 1
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const result = resultsByDate[dateStr]
    const isToday = dateStr === todayStr

    let cellClass = 'cal-day'
    if (result) {
      cellClass += result.is_correct ? ' cal-day-correct' : ' cal-day-incorrect'
    }
    if (isToday) cellClass += ' cal-day-today'

    return (
      <div key={dateStr} className={cellClass}>
        <span className="cal-day-number">{day}</span>
        {result && <span className="cal-day-dot" />}
      </div>
    )
  })

  return (
    <div className="calendar-container">
      <div className="calendar-header">
        <button className="cal-nav-btn" onClick={onPrevMonth} aria-label="Previous month">
          &#8249;
        </button>
        <span className="cal-month-label">{monthName} {year}</span>
        <button className="cal-nav-btn" onClick={onNextMonth} aria-label="Next month">
          &#8250;
        </button>
      </div>

      <div className="cal-grid">
        {DAY_LABELS.map((label, i) => (
          <div key={i} className="cal-day-header">{label}</div>
        ))}
        {blanks}
        {days}
      </div>
    </div>
  )
}

export default CalendarGrid
