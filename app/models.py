# pyright: basic
"""
Pydantic models for request/response validation.
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProblemModel(BaseModel):
    """Model for an integral problem."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    id: int = Field(..., ge=1, description="Problem ID")
    date: str = Field(..., description="Problem date in YYYY-MM-DD format")
    problem: str = Field(..., min_length=1, description="Problem statement (Unicode)")
    solution: str = Field(..., min_length=1, description="Solution (LaTeX)")
    hint: Optional[str] = Field(None, description="Single hint for the problem")
    difficulty: str = Field(..., description="Difficulty level")
    topic: Optional[str] = Field(None, description="Mathematical topic")
    latex_problem: Optional[str] = Field(None, description="Problem in LaTeX format")
    latex_solution: Optional[str] = Field(None, description="Solution in LaTeX format")
    integral_type: str = Field("indefinite", description="Whether the integral is 'definite' or 'indefinite'")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Update timestamp")
    progressive_hints: list[str] = Field(
        default_factory=list,
        description="List of progressive hints"
    )

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        """Validate difficulty is one of the allowed values."""
        allowed = {'easy', 'medium', 'hard'}
        if v.lower() not in allowed:
            raise ValueError(f"Difficulty must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date is in correct format."""
        try:
            # Try to parse as date to validate format
            year, month, day = map(int, v.split('-'))
            date(year, month, day)
            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got '{v}'") from e


class SubmissionRequest(BaseModel):
    """Model for answer submission request."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    answer: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's LaTeX answer"
    )
    problem: ProblemModel = Field(
        ...,
        description="The problem being answered"
    )

    @field_validator('answer')
    @classmethod
    def validate_answer_not_empty(cls, v: str) -> str:
        """Ensure answer is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Answer cannot be empty")
        return v.strip()


class SubmissionResponse(BaseModel):
    """Model for answer submission response."""

    model_config = ConfigDict(validate_assignment=True)

    success: bool = Field(..., description="Whether the request succeeded")
    is_correct: Optional[bool] = Field(None, description="Whether the answer is correct")
    message: str = Field(..., description="Feedback message")
    user_answer: Optional[str] = Field(None, description="User's answer in LaTeX")
    correct_answer: Optional[str] = Field(None, description="Correct answer in LaTeX")
    error: str | None = Field(None, description="Error message if any")


class ProblemResponse(BaseModel):
    """Model for problem fetch response."""

    model_config = ConfigDict(validate_assignment=True)

    success: bool = Field(..., description="Whether the request succeeded")
    problem: Optional[ProblemModel] = Field(None, description="Problem data")
    debug_mode: bool = Field(False, description="Whether debug mode is active")
    error: Optional[str] = Field(None, description="Error message if any")


class HealthResponse(BaseModel):
    """Model for health check response."""

    model_config = ConfigDict(validate_assignment=True)

    success: bool = Field(..., description="Whether API is healthy")
    message: str = Field(..., description="Status message")
