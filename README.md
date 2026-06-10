# Daily Integral Challenge
> *"An integral a day keeps the calculus away!"* 📈

A web application that presents daily calculus integration problems and validates LaTeX-formatted answers.

## Features
- A new integral problem every day, plus a practice archive of past problems
- LaTeX answer input (MathLive) with MathJax rendering
- Smart answer validation using SymPy (accepts equivalent forms)
- Progressive hints and a worked-solution reveal
- Accounts, streaks, and progress tracking via Supabase
- Light/dark themes and a shareable result card

## Quick Start
```bash
# Run backend + frontend together
./start.sh

# Or run them separately:
uv run python run.py      # backend → http://localhost:5000
cd frontend && npm install && npm run dev   # frontend → http://localhost:3000
```

## Tech Stack
- **Backend**: Flask, SymPy, Pydantic, Supabase (managed with `uv`)
- **Frontend**: React, Vite, MathLive, MathJax
- **Deploy**: Vercel via GitHub Actions

## Testing
```bash
uv run pytest app/tests/ migrations/tests/ -v   # backend
npm test --prefix frontend                        # frontend
```

Built with ❤️ for calculus enthusiasts everywhere.
