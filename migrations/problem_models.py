"""
Pydantic model for authoring new integral problems.

`NewProblem` is the authoring contract — what you write in the registry.
The runner converts it to a `ProblemModel` (app/models.py) before uploading,
so anything that passes here is guaranteed to be serveable by the API.

Fields intentionally omitted from authoring:
  - id, date      → auto-assigned by the runner at upload time
  - hint          → vestigial field, not rendered by the frontend
  - latex_problem,
    latex_solution → set to problem/solution at upload time
"""
from typing import Optional

import sympy as sp
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.utils import is_equivalent_up_to_constant, parse_latex_safely

X = sp.Symbol("x")


class NewProblem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, str_strip_whitespace=True)

    problem: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)
    integrand: sp.Expr = Field(..., description="SymPy integrand in x, used for verification only")
    integral_type: str = Field("indefinite")
    topic: str = Field(..., min_length=1)
    difficulty: str = Field(...)
    progressive_hints: list[str] = Field(..., min_length=1)

    # Required only for definite integrals.
    lower: Optional[sp.Expr] = None
    upper: Optional[sp.Expr] = None

    @field_validator("difficulty")
    @classmethod
    def _validate_difficulty(cls, v: str) -> str:
        allowed = {"easy", "medium", "hard"}
        if v.lower() not in allowed:
            raise ValueError(f"difficulty must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("integral_type")
    @classmethod
    def _validate_type(cls, v: str) -> str:
        allowed = {"indefinite", "definite"}
        if v.lower() not in allowed:
            raise ValueError(f"integral_type must be one of {allowed}, got '{v}'")
        return v.lower()

    @model_validator(mode="after")
    def _validate_bounds(self) -> "NewProblem":
        if self.integral_type == "definite" and (self.lower is None or self.upper is None):
            raise ValueError(f"definite integral '{self.problem}' requires lower and upper bounds")
        return self

    def verify(self) -> tuple[bool, str]:
        """
        Confirm the stored solution (a) parses with the app's LaTeX grader and
        (b) is equivalent to SymPy's own integration of the integrand.

        A PASS here means the app will accept the stored solution as correct at
        runtime — the same comparison logic is used in both places.
        """
        is_indef = self.integral_type == "indefinite"
        parsed = parse_latex_safely(self.solution, is_indefinite=is_indef)
        if parsed is None:
            return False, "solution LaTeX did not parse"

        # parse_latex renders e/pi as plain symbols; normalize so the comparison
        # against sympy.integrate() is mathematically meaningful.
        parsed = parsed.subs({sp.Symbol("e"): sp.E, sp.Symbol("pi"): sp.pi})

        try:
            if is_indef:
                truth = sp.integrate(self.integrand, X)
            else:
                truth = sp.integrate(self.integrand, (X, self.lower, self.upper))
        except Exception as exc:
            return False, f"sympy.integrate failed: {exc}"

        if truth is None or truth.has(sp.Integral):
            return False, "sympy could not evaluate the integral"

        ok = is_equivalent_up_to_constant(parsed, truth, is_indefinite=is_indef)
        return ok, ("OK" if ok else f"not equivalent (sympy truth: {truth})")

    def to_row(self, *, id: int, date: str) -> dict:
        """Build a Supabase row dict. id and date are assigned by the runner."""
        return {
            "id": id,
            "date": date,
            "problem": self.problem,
            "solution": self.solution,
            "hint": None,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "integral_type": self.integral_type,
            "progressive_hints": self.progressive_hints,
            # Mirror problem/solution into the legacy latex_* columns so any
            # code reading those fields gets consistent data.
            "latex_problem": self.problem,
            "latex_solution": self.solution,
        }
