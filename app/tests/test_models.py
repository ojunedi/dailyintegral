"""
Tests for Pydantic models and API validation.
"""
import pytest
from pydantic import ValidationError
from app.models import (
    ProblemModel,
    SubmissionRequest,
    SubmissionResponse,
    ProblemResponse,
    HealthResponse
)


class TestProblemModel:
    """Test ProblemModel validation."""

    def test_valid_problem(self):
        """Test creating a valid problem."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': r'\int x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'easy',
            'progressive_hints': ['Hint 1', 'Hint 2']
        }
        problem = ProblemModel(**problem_data)
        assert problem.id == 1
        assert problem.difficulty == 'easy'
        assert len(problem.progressive_hints) == 2

    def test_difficulty_validation(self):
        """Test that difficulty must be easy/medium/hard."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'EASY',  # Should be normalized to lowercase
        }
        problem = ProblemModel(**problem_data)
        assert problem.difficulty == 'easy'

    def test_invalid_difficulty(self):
        """Test that invalid difficulty raises ValidationError."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'super-hard',  # Invalid
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemModel(**problem_data)
        assert 'difficulty' in str(exc_info.value).lower()

    def test_invalid_date_format(self):
        """Test that invalid date format raises ValidationError."""
        problem_data = {
            'id': 1,
            'date': '01/01/2025',  # Wrong format
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'easy',
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemModel(**problem_data)
        assert 'date' in str(exc_info.value).lower()

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        problem_data = {
            'id': 1,
            # Missing date, problem, solution, difficulty
        }
        with pytest.raises(ValidationError) as exc_info:
            ProblemModel(**problem_data)
        errors = exc_info.value.errors()
        assert len(errors) >= 4  # At least 4 missing fields

    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'easy',
            # Omitting optional fields
        }
        problem = ProblemModel(**problem_data)
        assert problem.hint is None
        assert problem.topic is None
        assert problem.progressive_hints == []

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from strings."""
        problem_data = {
            'id': 1,
            'date': '  2025-01-01  ',
            'problem': '  ∫ x^2 dx  ',
            'solution': '  \\frac{x^3}{3} + C  ',
            'difficulty': '  easy  ',
        }
        problem = ProblemModel(**problem_data)
        assert problem.date == '2025-01-01'
        assert problem.problem == '∫ x^2 dx'
        assert problem.solution == '\\frac{x^3}{3} + C'
        assert problem.difficulty == 'easy'


class TestSubmissionRequest:
    """Test SubmissionRequest validation."""

    def test_valid_submission(self):
        """Test creating a valid submission request."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'easy',
        }
        submission_data = {
            'answer': r'\frac{x^3}{3} + C',
            'problem': problem_data
        }
        submission = SubmissionRequest(**submission_data)
        assert submission.answer == r'\frac{x^3}{3} + C'
        assert submission.problem.id == 1

    def test_empty_answer(self):
        """Test that empty answer raises ValidationError."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'easy',
        }
        submission_data = {
            'answer': '   ',  # Just whitespace
            'problem': problem_data
        }
        with pytest.raises(ValidationError) as exc_info:
            SubmissionRequest(**submission_data)
        assert 'answer' in str(exc_info.value).lower()

    def test_answer_too_long(self):
        """Test that answer longer than 1000 chars raises ValidationError."""
        problem_data = {
            'id': 1,
            'date': '2025-01-01',
            'problem': '∫ x^2 dx',
            'solution': r'\frac{x^3}{3} + C',
            'difficulty': 'easy',
        }
        submission_data = {
            'answer': 'x' * 1001,  # Too long
            'problem': problem_data
        }
        with pytest.raises(ValidationError) as exc_info:
            SubmissionRequest(**submission_data)
        assert 'answer' in str(exc_info.value).lower()


class TestSubmissionResponse:
    """Test SubmissionResponse model."""

    def test_correct_answer_response(self):
        """Test response for correct answer."""
        response = SubmissionResponse(
            success=True,
            is_correct=True,
            message='Correct! Well done!',
            user_answer=r'\frac{x^3}{3} + C',
            correct_answer=r'\frac{x^3}{3} + C'
        )
        assert response.success is True
        assert response.is_correct is True
        assert 'Correct' in response.message

    def test_incorrect_answer_response(self):
        """Test response for incorrect answer."""
        response = SubmissionResponse(
            success=True,
            is_correct=False,
            message='Incorrect. Try again!',
            user_answer=r'x^3',
            correct_answer=r'\frac{x^3}{3} + C'
        )
        assert response.success is True
        assert response.is_correct is False
        assert response.user_answer != response.correct_answer

    def test_error_response(self):
        """Test error response."""
        response = SubmissionResponse(
            success=False,
            message='Invalid input',
            error='Could not parse LaTeX'
        )
        assert response.success is False
        assert response.error is not None


class TestProblemResponse:
    """Test ProblemResponse model."""

    def test_successful_problem_fetch(self):
        """Test successful problem fetch response."""
        problem = ProblemModel(
            id=1,
            date='2025-01-01',
            problem='∫ x^2 dx',
            solution=r'\frac{x^3}{3} + C',
            difficulty='easy'
        )
        response = ProblemResponse(success=True, problem=problem)
        assert response.success is True
        assert response.problem is not None
        assert response.problem.id == 1

    def test_failed_problem_fetch(self):
        """Test failed problem fetch response."""
        response = ProblemResponse(
            success=False,
            error='No problem available'
        )
        assert response.success is False
        assert response.problem is None
        assert response.error is not None


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_health_response(self):
        """Test health check response."""
        response = HealthResponse(
            success=True,
            message='API is healthy'
        )
        assert response.success is True
        assert 'healthy' in response.message.lower()


class TestModelSerialization:
    """Test model serialization with model_dump()."""

    def test_problem_serialization(self):
        """Test that ProblemModel serializes correctly."""
        problem = ProblemModel(
            id=1,
            date='2025-01-01',
            problem='∫ x^2 dx',
            solution=r'\frac{x^3}{3} + C',
            difficulty='easy',
            progressive_hints=['Hint 1']
        )
        data = problem.model_dump()
        assert isinstance(data, dict)
        assert data['id'] == 1
        assert data['difficulty'] == 'easy'
        assert 'progressive_hints' in data

    def test_submission_response_serialization(self):
        """Test that SubmissionResponse serializes correctly."""
        response = SubmissionResponse(
            success=True,
            is_correct=True,
            message='Correct!',
            user_answer='x^3/3',
            correct_answer='x^3/3'
        )
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data['success'] is True
        assert data['is_correct'] is True
        assert 'message' in data
