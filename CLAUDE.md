# Daily Integral Challenge - Project Context

## Project Overview
This is a Flask-based "Daily Integral Challenge" web application that presents users with calculus integration problems and validates their LaTeX-formatted answers using SymPy.

## Project Structure
```
dailyintegral/
├── app/
│   ├── __init__.py          # Flask app factory with logging config and CORS setup
│   ├── api.py               # API endpoints for React frontend
│   ├── utils.py             # Math utilities (equivalence checking, LaTeX parsing)
│   ├── problem_source.py    # Abstract base classes and implementations for problem sources
│   ├── tests/
│   │   └── test_utils.py    # Unit tests for utils module
│   └── integrals.db         # SQLite database with problems (copy)
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API service layer
│   │   └── styles/          # CSS styles
│   ├── package.json         # Frontend dependencies
│   └── vite.config.js       # Frontend build configuration
├── .env/                    # Python virtual environment
├── integrals.db             # SQLite database with problems (main)
├── requirements.txt         # Python dependencies (pinned versions)
├── start.sh                 # Startup script for both servers
├── pytest.ini               # Test configuration
└── run.py                   # Application entry point
```

## Current Dependencies
### Backend (Flask)
- Flask 3.1.1
- Flask-CORS (for React frontend communication)
- SymPy 1.14.0 (mathematical computation)
- pytest 8.4.1 (testing)
- antlr4-python3-runtime 4.11.0 (LaTeX parsing)

### Frontend (React)
- React with Vite build system
- Tailwind CSS for styling
- MathJax/MathLive for mathematical input and display

## Key Issues Identified

### 1. Security Issues ✅ PARTIALLY ADDRESSED
- **SECRET_KEY**: `app/__init__.py:9` now uses environment variable with fallback ✅
- **SQL Injection**: `app/problem_source.py:103-106` uses parameterized queries ✅
- **Input validation**: LaTeX parsing includes error handling in `utils.py` ✅
- **CORS Configuration**: Added proper CORS setup for React frontend ✅

### 2. Code Quality Issues ✅ PARTIALLY ADDRESSED
- **Duplicate files**: `problem_source_new.py` has been removed ✅
- **Dead code**: Line 17 in `routes.py` still has commented DatabaseProblemSource ⚠️
- **Test failure**: Fixed equivalence checking logic bug (was differentiating w.r.t. constant C instead of variable x) ✅
- **Error handling**: Added try/catch blocks and proper database connection management ✅

### 3. Architecture Problems ✅ PARTIALLY ADDRESSED
- **Dependency injection**: Still hard-coded database paths ⚠️
- **Configuration management**: Added environment variable support for SECRET_KEY ✅
- **Logging strategy**: Implemented structured logging in `app/__init__.py` ✅
- **Database connections**: Using context managers for proper connection handling ✅
- **Frontend separation**: Added React frontend with API layer ✅

### 4. Production Features ✅ PARTIALLY ADDRESSED
- **requirements.txt**: Created with pinned versions ✅
- **Environment variables**: Added SECRET_KEY environment variable support ✅
- **Error pages**: Still using generic Flask error handling ❌
- **Rate limiting**: Not implemented ❌
- **HTTPS enforcement**: Not implemented ❌
- **CORS configuration**: Properly configured for React frontend ✅

### 5. Performance Issues ✅ PARTIALLY ADDRESSED
- **Frontend optimization**: React frontend with Vite build system ✅
- **CSS framework**: Using Tailwind CSS for optimized styling ✅
- **Caching**: No database query caching implemented ❌
- **CDN dependencies**: MathJax/MathLive still loaded from CDNs ❌

### 6. Testing & Development ⚠️ PARTIALLY ADDRESSED
- **Test coverage**: Utils module tested, 12/12 tests passing ✅
- **Integration tests**: Routes and database interaction untested ❌
- **Frontend tests**: No React component tests ❌
- **Linting setup**: No code quality enforcement ❌
- **CI/CD configuration**: Not implemented ❌

## Action Plan (Multi-Session Implementation)

### Phase 1: Critical Fixes ✅ COMPLETED (except test fix)
1. **Security vulnerabilities** ✅
   - Replace hard-coded SECRET_KEY with environment variable ✅
   - Fix SQL injection issues in database connections ✅
   - Add input validation for LaTeX parsing ✅

2. **Code cleanup** ✅ PARTIALLY COMPLETED
   - Remove duplicate `problem_source_new.py` file ✅
   - Clean up dead code in `routes.py` ⚠️ (commented line remains)
   - Fix failing test in `test_utils.py` ✅ (all 12 tests passing)

3. **Frontend modernization** ✅ COMPLETED
   - Added React frontend with Vite build system ✅
   - Implemented API layer for backend communication ✅
   - Added CORS configuration ✅

### Phase 2: UI/UX Enhancement ❌ NEXT IMMEDIATE PHASE
1. **User Interface Improvements**
   - Redesign and enhance the current React frontend
   - Improve user experience and visual design
   - Add responsive design features
   - Enhance mathematical input/output display
   - Add user feedback and interaction improvements

2. **Frontend Feature Enhancements**
   - Add progress tracking for users
   - Implement hint system for difficult problems
   - Add problem difficulty indicators
   - Create better error messaging and validation feedback
   - Add accessibility improvements

### Phase 3: Configuration & Dependencies ❌ NEEDS COMPLETION
1. **Configuration management** ⚠️ PARTIALLY COMPLETED
   - Create `requirements.txt` ✅ (created with pinned versions)
   - Add environment variable support ✅ (SECRET_KEY implemented)
   - Create configuration classes for different environments ❌

2. **Database improvements** ✅ PARTIALLY COMPLETED
   - Implement proper connection pooling ✅ (using context managers)
   - Add database migration support ❌
   - Improve error handling ✅ (try/catch blocks added)

### Phase 4: Testing & Quality
5. **Comprehensive testing**
   - Add integration tests for routes
   - Add database tests
   - Improve test coverage
   - Set up linting (flake8, black, mypy)

6. **Error handling & logging**
   - Add proper exception handling
   - Implement structured logging
   - Create custom error pages

### Phase 5: Production Readiness
7. **Production deployment**
   - Add WSGI configuration
   - Environment-specific settings
   - Docker configuration
   - Static file optimization

8. **Performance & Security**
   - Implement caching
   - Add rate limiting
   - HTTPS enforcement
   - CORS configuration

## Testing Commands
```bash
# Activate virtual environment
source .env/bin/activate

# Run tests
./.env/bin/pytest app/tests/ -v

# Run application
./.env/bin/python run.py
```

## Current Test Status
- **Backend Tests**: 12/12 tests passing ✅
- **Test Fix**: Fixed `test_integration_examples` equivalence checking bug ✅
- **Dependency Note**: antlr4-python3-runtime must be 4.11.x (not latest) for SymPy LaTeX parsing ✅

## Known Issues / Gotchas
- **macOS Port 5000 Conflict**: AirPlay Receiver uses port 5000 by default. If you get 403 errors, disable it: System Settings → General → AirDrop & Handoff → AirPlay Receiver → OFF
- **Frontend Tests**: No React component tests implemented ❌
- **Integration Tests**: No API endpoint tests implemented ❌

## Current Architecture
- **Backend**: Flask API with SQLite database
- **Frontend**: React with Vite build system, Tailwind CSS
- **Math Processing**: SymPy for expression parsing and equivalence checking
- **Math Display**: MathJax for rendering, MathLive for input
- **Database**: SQLite with `integrals` table containing problems
- **API Communication**: REST endpoints with CORS enabled
- After any changes are made look in the CLAUDE.md if any TODOs or things have been completed and update it accordingly
- Claude is allowed to edit CLAUDE.md to keep project status current