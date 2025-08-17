from flask import Blueprint, jsonify, request, current_app
from app.problem_source import StaticProblemSource, DatabaseProblemSource
from app.utils import is_equivalent_up_to_constant, parse_latex_safely

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/problem', methods=['GET'])
def get_today_problem():
    """
    Get today's integral problem as JSON.
    """
    try:
        problem_source = StaticProblemSource()
        problem = problem_source.get_today_problem()
        
        if problem:
            current_app.logger.info(f"API: Today's problem: {problem}")
            return jsonify({
                'success': True,
                'problem': problem
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No problem available for today'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"API: Error fetching problem: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/submit', methods=['POST'])
def submit_answer():
    """
    Submit and validate an answer.
    """
    try:
        data = request.get_json()
        
        if not data or 'answer' not in data:
            return jsonify({
                'success': False,
                'error': 'Answer is required'
            }), 400
        
        user_answer_latex = data['answer']
        current_app.logger.info(f"API: User answer (raw): {user_answer_latex}")
        
        # Get the correct answer
        problem_source = StaticProblemSource()
        problem = problem_source.get_today_problem()
        
        if not problem:
            return jsonify({
                'success': False,
                'error': 'No problem available'
            }), 404
        
        # Parse user answer and correct answer safely
        user_answer = parse_latex_safely(user_answer_latex)
        true_answer = parse_latex_safely(problem['solution'])
        
        if user_answer is None:
            return jsonify({
                'success': False,
                'error': 'Invalid mathematical expression. Please check your input.',
                'is_correct': False
            })
        elif true_answer is None:
            current_app.logger.error(f"Failed to parse correct answer: {problem['solution']}")
            return jsonify({
                'success': False,
                'error': 'Error processing the correct answer. Please contact support.',
                'is_correct': False
            }), 500
        else:
            current_app.logger.info(f"Parsed user answer: {user_answer}")
            current_app.logger.info(f"Parsed correct answer: {true_answer}")
            
            # Validate the answer
            is_correct = is_equivalent_up_to_constant(user_answer, true_answer)
            
            return jsonify({
                'success': True,
                'is_correct': is_correct,
                'message': 'Correct! Well done!' if is_correct else 'Incorrect. Try again!',
                'user_answer': str(user_answer),
                'correct_answer': str(true_answer)
            })
            
    except Exception as e:
        current_app.logger.error(f"API: Error processing answer: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint.
    """
    return jsonify({
        'success': True,
        'message': 'API is healthy'
    })