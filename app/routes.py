from logging import Logger
from flask import Blueprint, Flask, render_template, request, flash, current_app
import flask
from app.problem_source import StaticProblemSource, DatabaseProblemSource
from app.utils import is_equivalent_up_to_constant, parse_latex_safely
import sympy as sp

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Handle the main page of the application.
    GET: Display the daily integral problem
    POST: Process the user's answer submission
    """
    # problem_source = DatabaseProblemSource("integrals.db")
    problem_source = StaticProblemSource()
    problem = problem_source.get_today_problem()
    current_app.logger.info(f"Today's problem: {problem}")

    if request.method == 'POST':
        user_answer_latex = request.form.get('answer', '')
        current_app.logger.info(f"User answer (raw): {user_answer_latex}")
        
        # Parse user answer and correct answer safely
        user_answer = parse_latex_safely(user_answer_latex)
        true_answer = parse_latex_safely(problem['solution'])
        
        if user_answer is None:
            flash('Invalid mathematical expression. Please check your input.', 'error')
        elif true_answer is None:
            flash('Error processing the correct answer. Please contact support.', 'error')
            current_app.logger.error(f"Failed to parse correct answer: {problem['solution']}")
        else:
            current_app.logger.info(f"Parsed user answer: {user_answer}")
            current_app.logger.info(f"Parsed correct answer: {true_answer}")
            
            # Validate the answer
            is_correct = is_equivalent_up_to_constant(user_answer, true_answer)
            
            if is_correct:
                flash('Correct! Well done!', 'success')
            else:
                flash('Incorrect. Try again!', 'error')



    return render_template('index.html', problem=problem)

