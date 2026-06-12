# pyright: basic
# pyright: reportCallIssue=false
from typing import Tuple, Union

from flask import Blueprint, Response, current_app, g, jsonify, request
from pydantic import ValidationError

from app import limiter
from app.ai_hint import generate_hint
from app.auth import require_auth
from app.models import (
    HealthResponse,
    HintRequest,
    HintResponse,
    ProblemModel,
    ProblemResponse,
    ProgressEntry,
    SubmissionRequest,
    SubmissionResponse,
    SyncRequest,
)
from app.problem_source import DatabaseProblemSource, SupabaseProblemSource
from app.progress import get_progress, save_progress, sync_progress
from app.utils import (
    has_constant_of_integration,
    is_equivalent_up_to_constant,
    parse_latex_safely,
    sympy_to_latex,
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

def _get_db_path():
    return current_app.config['DATABASE_PATH']


def _get_problem_source():
    """Build the configured problem source: Supabase (default) or local SQLite."""
    if current_app.config.get('PROBLEM_SOURCE') == 'sqlite':
        return DatabaseProblemSource(_get_db_path())
    return SupabaseProblemSource(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_KEY'],
    )


@api_bp.route('/problem', methods=['GET'])
def get_today_problem() -> Union[Response, Tuple[Response, int]]:
    """
    Get today's integral problem as JSON.

    Returns:
        Response or tuple: JSON response with problem data or error
    """
    try:
        debug_mode = current_app.config.get('DEBUG_MODE', False)
        problem_source = _get_problem_source()

        if debug_mode:
            problem_data = problem_source.get_random_problem()
        else:
            problem_data = problem_source.get_daily_problem()

        if problem_data:
            try:
                problem = ProblemModel(**problem_data)
                response = ProblemResponse(
                    success=True,
                    problem=problem,
                    debug_mode=debug_mode,
                    ai_hints_enabled=bool(current_app.config.get('ANTHROPIC_API_KEY')),
                )
                current_app.logger.info(
                    f"API: Serving problem {problem.id} "
                    f"({'debug/random' if debug_mode else 'daily'})"
                )
                return jsonify(response.model_dump())
            except ValidationError as e:
                current_app.logger.error(f"Problem validation error: {e}")
                problem = ProblemModel(**problem_data)
                response = ProblemResponse(
                    success=False,
                    problem=problem,
                    debug_mode=debug_mode,
                    error="Problem data validation failed"
                )
                return jsonify(response.model_dump()), 500
        else:
            response = ProblemResponse(
                success=False,
                problem=None,
                debug_mode=debug_mode,
                error='No problem available for today'
            )
            return jsonify(response.model_dump()), 404

    except Exception as e:
        current_app.logger.error(f"API: Error fetching problem: {e}")
        response = ProblemResponse(
            success=False,
            problem=None,
            error='Internal server error'
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/practice/problem', methods=['GET'])
def get_practice_problem() -> Union[Response, Tuple[Response, int]]:
    """
    Get a random practice problem as JSON.

    Practice problems are independent of the daily challenge: they do not affect
    the daily streak or progress (the client simply never POSTs progress for
    practice attempts). Grading reuses the stateless POST /api/submit endpoint.

    Optional query params:
        difficulty: filter to 'easy' | 'medium' | 'hard'
        topic: filter to a specific topic

    Returns:
        Response or tuple: JSON response with problem data or error
    """
    try:
        difficulty = request.args.get('difficulty') or None
        topic = request.args.get('topic') or None

        if difficulty and difficulty.lower() not in {'easy', 'medium', 'hard'}:
            response = ProblemResponse(
                success=False,
                problem=None,
                error="difficulty must be one of 'easy', 'medium', 'hard'",
            )
            return jsonify(response.model_dump()), 400

        problem_source = _get_problem_source()
        problem_data = problem_source.get_random_problem(
            difficulty=difficulty.lower() if difficulty else None,
            topic=topic,
        )

        if problem_data:
            problem = ProblemModel(**problem_data)
            response = ProblemResponse(success=True, problem=problem)
            current_app.logger.info(f"API: Serving practice problem {problem.id}")
            return jsonify(response.model_dump())

        response = ProblemResponse(
            success=False,
            problem=None,
            error='No practice problem available',
        )
        return jsonify(response.model_dump()), 404

    except Exception as e:
        current_app.logger.error(f"API: Error fetching practice problem: {e}")
        response = ProblemResponse(
            success=False,
            problem=None,
            error='Internal server error',
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/submit', methods=['POST'])
@limiter.limit("20 per minute")
def submit_answer() -> Union[Response, tuple[Response, int]]:
    """
    Submit and validate an answer.

    Returns:
        Response or tuple: JSON response with validation result
    """
    try:
        data = request.get_json()

        if not data:
            response = SubmissionResponse(
                success=False,
                message='No data provided',
                error='Request body is required'
            )
            return jsonify(response.model_dump()), 400

        # Validate request with Pydantic
        try:
            submission = SubmissionRequest(**data)
        except ValidationError as e:
            current_app.logger.warning(f"Validation error: {e}")
            response = SubmissionResponse(
                success=False,
                message='Invalid request data',
                error=str(e.errors()[0]['msg'])
            )
            return jsonify(response.model_dump()), 400

        current_app.logger.info(f"API: User answer (raw): {submission.answer}")
        current_app.logger.info(f"API: Problem ID: {submission.problem.id}")

        # Parse user answer and correct answer safely
        is_indefinite = submission.problem.integral_type != 'definite'

        # For indefinite integrals, missing +C is immediately incorrect
        if is_indefinite and not has_constant_of_integration(submission.answer):
            true_answer = parse_latex_safely(submission.problem.solution)
            response = SubmissionResponse(
                success=True,
                is_correct=False,
                message='Incorrect. Try again!',
                user_answer=submission.answer,
                correct_answer=sympy_to_latex(true_answer, is_indefinite=is_indefinite) if true_answer else None,
            )
            return jsonify(response.model_dump())

        user_answer = parse_latex_safely(submission.answer)
        true_answer = parse_latex_safely(submission.problem.solution)

        if user_answer is None:
            response = SubmissionResponse(
                success=False,
                is_correct=False,
                message='Invalid mathematical expression',
                error='Could not parse your answer. Please check LaTeX syntax.'
            )
            return jsonify(response.model_dump())

        if true_answer is None:
            current_app.logger.error(
                f"Failed to parse correct answer: {submission.problem.solution}"
            )
            response = SubmissionResponse(
                success=False,
                is_correct=False,
                message='Server error',
                error='Error processing the correct answer'
            )
            return jsonify(response.model_dump()), 500

        current_app.logger.info(f"Parsed user answer: {user_answer}")
        current_app.logger.info(f"Parsed correct answer: {true_answer}")

        # Validate the answer
        is_correct: bool = is_equivalent_up_to_constant(user_answer, true_answer, is_indefinite=is_indefinite)

        response = SubmissionResponse(
            success=True,
            is_correct=is_correct,
            message='Correct! Well done!' if is_correct else 'Incorrect. Try again!',
            user_answer=sympy_to_latex(user_answer, is_indefinite=is_indefinite),
            correct_answer=sympy_to_latex(true_answer, is_indefinite=is_indefinite)
        )
        return jsonify(response.model_dump())

    except Exception as e:
        current_app.logger.error(f"API: Error processing answer: {e}")
        response = SubmissionResponse(
            success=False,
            message='Internal server error',
            error=str(e)
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/hint', methods=['POST'])
@limiter.limit("5 per minute")
def get_ai_hint() -> Union[Response, Tuple[Response, int]]:
    """
    Generate an on-demand AI hint tailored to the user's current attempt.

    The attempt is first analyzed symbolically with SymPy (missing +C,
    coefficient off by a factor, sign error, derivative mismatch); those
    grounded findings are then turned into a single targeted nudge by Claude.
    The model never sees the stored solution, so it cannot leak it verbatim.

    Stateless like /submit — never touches progress or the daily streak.
    """
    api_key = current_app.config.get('ANTHROPIC_API_KEY')
    if not api_key:
        response = HintResponse(success=False, error='AI hints are not configured')
        return jsonify(response.model_dump()), 503

    data = request.get_json(silent=True)
    if not data:
        response = HintResponse(success=False, error='Request body is required')
        return jsonify(response.model_dump()), 400

    try:
        hint_req = HintRequest(**data)
    except ValidationError as e:
        current_app.logger.warning(f"Hint validation error: {e}")
        response = HintResponse(success=False, error=str(e.errors()[0]['msg']))
        return jsonify(response.model_dump()), 400

    try:
        hint = generate_hint(hint_req.problem, hint_req.attempt, api_key)
    except Exception as e:
        current_app.logger.error(f"API: Error generating hint: {e}")
        response = HintResponse(success=False, error='Hint service is temporarily unavailable')
        return jsonify(response.model_dump()), 502

    if not hint:
        response = HintResponse(success=False, error='Could not generate a hint for this attempt')
        return jsonify(response.model_dump()), 502

    current_app.logger.info(f"API: Generated AI hint for problem {hint_req.problem.id}")
    response = HintResponse(success=True, hint=hint)
    return jsonify(response.model_dump())


@api_bp.route('/progress', methods=['POST'])
@limiter.limit("30 per minute")
@require_auth
def save_user_progress() -> Union[Response, Tuple[Response, int]]:
    """Save a daily result for the authenticated user."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        try:
            entry = ProgressEntry(**data)
        except ValidationError as e:
            return jsonify({'success': False, 'error': str(e.errors()[0]['msg'])}), 400

        save_progress(g.user_id, entry.date, entry.problem_id, entry.is_correct, entry.difficulty)
        return jsonify({'success': True, 'message': 'Progress saved'})
    except Exception as e:
        current_app.logger.error(f"Error saving progress: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@api_bp.route('/progress', methods=['GET'])
@limiter.limit("30 per minute")
@require_auth
def get_user_progress() -> Union[Response, Tuple[Response, int]]:
    """Get all progress for the authenticated user."""
    try:
        results = get_progress(g.user_id)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        current_app.logger.error(f"Error fetching progress: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@api_bp.route('/progress/sync', methods=['POST'])
@limiter.limit("5 per minute")
@require_auth
def sync_user_progress() -> Union[Response, Tuple[Response, int]]:
    """Bulk upload localStorage results for the authenticated user."""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        try:
            sync_req = SyncRequest(**data)
        except ValidationError as e:
            return jsonify({'success': False, 'error': str(e.errors()[0]['msg'])}), 400

        sync_progress(g.user_id, [e.model_dump() for e in sync_req.entries])
        return jsonify({'success': True, 'message': f'Synced {len(sync_req.entries)} entries'})
    except Exception as e:
        current_app.logger.error(f"Error syncing progress: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@api_bp.route('/health', methods=['GET'])
def health_check() -> Response:
    """
    Simple health check endpoint.

    Returns:
        Response: JSON response indicating API health
    """
    response = HealthResponse(
        success=True,
        message='API is healthy'
    )
    return jsonify(response.model_dump())
