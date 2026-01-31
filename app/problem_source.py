import sqlite3
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import date

class ProblemSource(ABC):
    """
    Abstract base class for problem sources.
    Defines the interface that all problem sources must implement.
    """

    @abstractmethod
    def get_today_problem(self) -> Optional[Dict[str, Any]]:
        """
        Return today's integral problem.

        Returns:
            dict or None: A dictionary containing the problem details or None if no problem is available
        """
        pass


class BaseProblemSource(ProblemSource):
    """
    Base implementation of ProblemSource that provides common functionality
    for concrete problem source implementations.
    """

    def __init__(self):
        """Initialize the base problem source."""
        pass

    def format_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the problem data into a standardized dictionary.

        Args:
            problem: Raw problem data (could be a tuple from DB or a dict)

        Returns:
            dict: A standardized problem dictionary
        """
        # Default implementation returns the problem as is
        # Subclasses can override this to provide custom formatting
        return problem


class StaticProblemSource(BaseProblemSource):
    """
    A static source of integral problems.
    This class will be replaced with a database-backed implementation later.
    """

    def __init__(self):
        """Initialize with a hardcoded problem."""
        super().__init__()
        # Hardcoded example problem
        self.problem = {
            'id': 1,
            'date': '2025-06-16',
            'problem': r'\int x^2 dx',
            'solution': r'\frac{x^3}{3}',
            'difficulty': 'easy',
            'hint': r'\text{Use the power rule:} \int x^n dx = \frac{x^{n+1}}{n+1} + C',
            'progressive_hints':[
                r'\text{Look at the form of integrand}',
                r'\text{It is a power function}',
                r'\text{Use the power rule:} \int x^n dx = \frac{x^{n+1}}{n+1} + C'
            ]
        }

    def get_today_problem(self) -> Dict[str, Any]:
        """
        Return today's integral problem.

        Returns:
            dict: A dictionary containing the problem details
        """
        # In a real implementation, this would fetch from a database based on the current date
        return self.format_problem(self.problem)


class DatabaseProblemSource(BaseProblemSource):
    """
    A database-backed source of integral problems.
    Fetches problems from a SQLite database.
    """

    def __init__(self, db_name: str):
        """
        Initialize with a database connection.

        Args:
            db_name (str): Path to the SQLite database file
        """
        super().__init__()
        self.db_name = db_name

    def format_problem(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the problem data from database, parsing JSON fields.
        
        Args:
            problem: Raw problem data from database
            
        Returns:
            dict: Formatted problem dictionary with parsed JSON fields
        """
        if 'progressive_hints' in problem and problem['progressive_hints']:
            try:
                # Parse the JSON string into a Python list
                problem['progressive_hints'] = json.loads(problem['progressive_hints'])
            except (json.JSONDecodeError, TypeError) as e:
                # If parsing fails, fall back to empty list
                print(f"Error parsing progressive_hints: {e}")
                problem['progressive_hints'] = []
        
        # Fix LaTeX backslash escaping issues
        latex_fields = ['solution', 'latex_problem', 'latex_solution']
        for field in latex_fields:
            if field in problem and problem[field]:
                # Replace double backslashes with single backslashes for LaTeX functions
                value = problem[field]
                value = value.replace('\\\\', '\\')
                problem[field] = value
        
        return problem

    def get_random_problem(self) -> Optional[Dict[str, Any]]:

        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM integrals ORDER BY RANDOM() LIMIT 1")
                problem = cursor.fetchone()

                if problem:
                    # Convert the tuple to a dictionary with column names
                    columns = [col[0] for col in cursor.description]
                    problem_dict = dict(zip(columns, problem))
                    return self.format_problem(problem_dict)

        except sqlite3.Error as e:
            # Log the error (in a real app, use proper logging)
            print(f"Database error: {e}")

        return None

    def get_today_problem(self) -> Optional[Dict[str, Any]]:
        """
        Return today's integral problem from the database.

        Returns:
            dict or None: A dictionary containing the problem details or None if no problem found
        """
        try:
            # Create a new connection for this request (thread-safe)
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                today = date.today().strftime('%Y-%m-%d')
                cursor.execute("SELECT * FROM integrals WHERE date = ?", (today,))
                problem = cursor.fetchone()

                if problem:
                    # Convert the tuple to a dictionary with column names
                    columns = [col[0] for col in cursor.description]
                    problem_dict = dict(zip(columns, problem))
                    return self.format_problem(problem_dict)

        except sqlite3.Error as e:
            # Log the error (in a real app, use proper logging)
            print(f"Database error: {e}")

        return None
