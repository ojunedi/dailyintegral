from flask import Blueprint, jsonify, request, current_app, Response
from typing import Union, Tuple
from pydantic import ValidationError
from app.problem_source import DatabaseProblemSource
from app.utils import is_equivalent_up_to_constant, parse_latex_safely, sympy_to_latex
from app.models import (
    ProblemModel,
    SubmissionRequest,
    SubmissionResponse,
    ProblemResponse,
    HealthResponse
)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/problem', methods=['GET'])
def get_today_problem() -> Union[Response, Tuple[Response, int]]:
    """
    Get today's integral problem as JSON.

    Returns:
        Response or tuple: JSON response with problem data or error
    """
    try:
        problem_source = DatabaseProblemSource('integrals.db')
        problem_data = problem_source.get_random_problem()

        if problem_data:
            # Validate with Pydantic
            try:
                problem = ProblemModel(**problem_data)
                response = ProblemResponse(success=True, problem=problem)
                current_app.logger.info(f"API: Today's problem: {problem.id}")
                return jsonify(response.model_dump())
            except ValidationError as e:
                current_app.logger.error(f"Problem validation error: {e}")
                response = ProblemResponse(
                    success=False,
                    problem=problem_data,
                    error="Problem data validation failed"
                )
                return jsonify(response.model_dump()), 500
        else:
            response = ProblemResponse(
                success=False,
                problem=problem_data,
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
def submit_answer() -> Union[Response, Tuple[Response, int]]:
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
        is_correct: bool = is_equivalent_up_to_constant(user_answer, true_answer)

        response = SubmissionResponse(
            success=True,
            is_correct=is_correct,
            message='Correct! Well done!' if is_correct else 'Incorrect. Try again!',
            user_answer=sympy_to_latex(user_answer),
            correct_answer=sympy_to_latex(true_answer)
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
