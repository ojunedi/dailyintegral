# Daily Integral Challenge
> *"An integral a day keeps the calculus away!"* 📈

A web application that presents daily calculus integration problems and validates LaTeX-formatted answers.

## Features
- Daily integral problems from SQLite database
- LaTeX input with MathJax rendering
- Smart answer validation using SymPy (accepts equivalent forms)
- Modern React frontend with Flask API backend

## Quick Start
```bash
# Backend
source env/bin/activate
python run.py

# Frontend
cd frontend
npm install
npm run dev
```

## Tech Stack
- **Backend**: Flask, SymPy, SQLite
- **Frontend**: React, Vite, Tailwind CSS
- **Math**: MathJax, LaTeX parsing

## Testing
```bash
python -m pytest app/tests/ -v
```

Built with ❤️ for calculus enthusiasts everywhere.