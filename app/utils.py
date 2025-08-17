import sympy as sp
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def is_equivalent_up_to_constant(user_answer: Optional[sp.Expr], correct_answer: Optional[sp.Expr]) -> bool:
    """
    Check if the user's answer is equivalent to the correct answer up to a constant.

    Args:
        user_answer (sympy.Expr or None): The answer provided by the user
        correct_answer (sympy.Expr or None): The correct answer from the problem source

    Returns:
        bool: True if the answers are equivalent up to a constant, False otherwise
    """
    if user_answer is None or correct_answer is None:
        logger.warning("One of the answers is None")
        return False
    
    try:
        # Convert to sympy expressions if they're not already
        user_answer = sp.sympify(user_answer)
        correct_answer = sp.sympify(correct_answer)
        
        # Method 1: Check if derivatives are equal (eliminates constants)
        # Find the variable in the expression (usually 'x' for integrals)
        variables = user_answer.free_symbols.union(correct_answer.free_symbols)
        if not variables:
            # If no variables, both are constants - they're equivalent up to a constant
            return True
        
        # Filter out constant symbols and use main variable (typically 'x')
        main_variables = variables - {sp.Symbol('C')}
        if not main_variables:
            # If only constant symbols, they're equivalent up to a constant
            return True
        
        # Use the first main variable found (typically 'x')
        var = list(main_variables)[0]
        
        user_derivative = sp.diff(user_answer, var)
        correct_derivative = sp.diff(correct_answer, var)
        
        # Simplify and check if derivatives are equal
        difference = sp.simplify(user_derivative - correct_derivative)
        
        logger.info(f"User derivative: {user_derivative}")
        logger.info(f"Correct derivative: {correct_derivative}")
        logger.info(f"Derivative difference: {difference}")
        
        # Check if the difference is zero
        if difference == 0:
            return True
        
        # Method 2: Fallback - check if difference is constant
        # This handles edge cases where derivatives might not work
        expr_difference = sp.simplify(user_answer - correct_answer)
        logger.info(f"Expression difference: {expr_difference}")
        
        # Check if the difference contains no variables (i.e., is constant)
        # Exclude the constant symbol 'C' from consideration
        difference_vars = expr_difference.free_symbols - {sp.Symbol('C')}
        is_constant = len(difference_vars) == 0
        
        return is_constant
        
    except Exception as e:
        logger.error(f"Error in equivalence checking: {e}")
        return False


def parse_latex_safely(latex_str: str) -> Optional[sp.Expr]:
    """
    Safely parse LaTeX string to sympy expression with error handling.
    
    Args:
        latex_str (str): LaTeX string to parse
        
    Returns:
        sympy.Expr or None: Parsed expression or None if parsing fails
    """
    if not latex_str or not latex_str.strip():
        return None
    
    # Input validation - check for potentially dangerous content
    latex_str = latex_str.strip()
    
    # Check length to prevent DoS attacks
    if len(latex_str) > 1000:
        logger.warning(f"LaTeX input too long: {len(latex_str)} characters")
        return None
    
    # Check for potentially dangerous patterns
    dangerous_patterns = [
        '\\input', '\\include', '\\write', '\\read', '\\openin', '\\openout',
        '\\immediate', '\\special', '\\catcode', '\\def', '\\let'
    ]
    latex_lower = latex_str.lower()
    for pattern in dangerous_patterns:
        if pattern in latex_lower:
            logger.warning(f"Potentially dangerous LaTeX command detected: {pattern}")
            return None
        
    try:
        from sympy.parsing.latex import parse_latex
        
        # Clean up common LaTeX issues
        latex_str = latex_str.strip()
        
        # Handle missing +C case - add it if not present
        if '+C' not in latex_str and '+ C' not in latex_str and '-C' not in latex_str and '- C' not in latex_str:
            # Check if this looks like an integral result (no equals sign)
            if '=' not in latex_str:
                latex_str = latex_str + ' + C'
        
        parsed_expr = parse_latex(latex_str)
        logger.info(f"Successfully parsed LaTeX: {latex_str} -> {parsed_expr}")
        return parsed_expr
        
    except Exception as e:
        logger.error(f"Failed to parse LaTeX '{latex_str}': {e}")
        return None



# class ConstantOfIntegration(sp.NumberSymbol):
#     def __new__(self, name):
#         obj = sp.NumberSymbol.__new__(self)
#         obj._name = name
#         return obj
#
#     __str__ = lambda self: str(self._name)
