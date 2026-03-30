# pyright: basic
# pyright: reportCallIssue=false
from flask import Blueprint, jsonify, request, current_app, Response
from typing import Union, Tuple
from pydantic import ValidationError
from app.problem_source import DatabaseProblemSource
from app.utils import is_equivalent_up_to_constant, parse_latex_safely, sympy_to_latex, has_constant_of_integration
from app import limiter
from app.models import (
    ProblemModel,
    SubmissionRequest,
    SubmissionResponse,
    ProblemResponse,
    HealthResponse
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

def _get_db_path():
    return current_app.config['DATABASE_PATH']


@api_bp.route('/problem', methods=['GET'])
def get_today_problem() -> Union[Response, Tuple[Response, int]]:
    """
    Get today's integral problem as JSON.

    Returns:
        Response or tuple: JSON response with problem data or error
    """
    try:
        debug_mode = current_app.config.get('DEBUG_MODE', False)
        problem_source = DatabaseProblemSource(_get_db_path())

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
                    debug_mode=debug_mode
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
            true_answer = parse_latex_safely(submission.problem.solution, is_indefinite=is_indefinite)
            response = SubmissionResponse(
                success=True,
                is_correct=False,
                message='Incorrect. Try again!',
                user_answer=submission.answer,
                correct_answer=sympy_to_latex(true_answer, is_indefinite=is_indefinite) if true_answer else None,
            )
            return jsonify(response.model_dump())

        user_answer = parse_latex_safely(submission.answer, is_indefinite=is_indefinite)
        true_answer = parse_latex_safely(submission.problem.solution, is_indefinite=is_indefinite)

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
        is_correct: bool = is_equivalent_up_to_constant(user_answer, true_answer)

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
