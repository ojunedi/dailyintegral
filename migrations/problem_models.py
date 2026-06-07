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

from app.utils import expressions_match_numerically, parse_latex_safely

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

    # Escape hatch for definite integrals whose value is a textbook result but
    # whose numeric quadrature does not converge (e.g. Dirichlet's sin(x)/x over
    # [0, oo)). When True, verify() falls back to symbolic sympy.integrate
    # comparison. Use sparingly and only for hand-checked, famous results.
    trusted: bool = False

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
        Confirm the stored solution is correct by checking it against the
        *integrand* directly — independent of sympy.integrate(), which can
        silently return a wrong closed form (e.g. it returns 0 for
        \\int 1/(x^8+1) dx).

          - indefinite: d/dx(solution) must equal the integrand. Differentiation
            is algorithmic, so this is a trustworthy independent gate.
          - definite: the solution's value must match mpmath numeric quadrature
            of the integrand. Quadrature does not route through the symbolic
            integrate() that has the bug.

        A PASS here means the app will accept the stored solution as correct at
        runtime.
        """
        is_indef = self.integral_type == "indefinite"
        parsed = parse_latex_safely(self.solution, is_indefinite=is_indef)
        if parsed is None:
            return False, "solution LaTeX did not parse"

        # parse_latex renders e/pi as plain symbols; normalize before comparison.
        parsed = parsed.subs({sp.Symbol("e"): sp.E, sp.Symbol("pi"): sp.pi})

        if is_indef:
            return self._verify_indefinite(parsed)
        return self._verify_definite(parsed)

    def _verify_indefinite(self, parsed: sp.Expr) -> tuple[bool, str]:
        """d/dx(solution) must equal the integrand (the +C drops out)."""
        derivative = sp.diff(parsed, X)
        try:
            result = derivative.equals(self.integrand)
        except Exception:  # noqa: BLE001
            result = None
        if result is True:
            return True, "OK"
        if result is False:
            return False, "d/dx(solution) != integrand"
        # .equals() returns None when it can't decide (common for tan(x/2) and
        # floor-carrying antiderivatives). Fall back to numeric sampling — never
        # treat the symbolic "inconclusive" as a pass.
        return self._numeric_derivative_match(derivative)

    def _numeric_derivative_match(self, derivative: sp.Expr) -> tuple[bool, str]:
        """Confirm d/dx(solution) == integrand via the shared numeric primitive."""
        if expressions_match_numerically(derivative, self.integrand):
            return True, "OK (numeric)"
        return False, "could not confirm d/dx(solution) == integrand (numeric)"

    def _verify_definite(self, parsed: sp.Expr) -> tuple[bool, str]:
        """The solution value must match numeric quadrature of the integrand."""
        if parsed.free_symbols:
            return False, f"definite answer has free symbols: {parsed.free_symbols}"

        if self.trusted:
            return self._verify_definite_symbolic(parsed)

        try:
            numeric = sp.Integral(self.integrand, (X, self.lower, self.upper)).evalf()
            target = complex(parsed.evalf())
        except Exception as exc:  # noqa: BLE001
            return False, f"numeric check raised: {exc} (set trusted=True if textbook)"

        if not getattr(numeric, "is_number", False) or numeric.has(sp.Integral, sp.nan, sp.zoo):
            return False, "numeric quadrature did not converge (set trusted=True if textbook)"

        diff = abs(complex(numeric) - target)
        scale = max(1.0, abs(target))
        if diff / scale < 1e-6:
            return True, "OK"
        return False, f"value {target} != numeric integral {complex(numeric)}"

    def _verify_definite_symbolic(self, parsed: sp.Expr) -> tuple[bool, str]:
        """Fallback for trusted textbook definite integrals: symbolic compare."""
        try:
            truth = sp.integrate(self.integrand, (X, self.lower, self.upper))
        except Exception as exc:  # noqa: BLE001
            return False, f"sympy.integrate failed: {exc}"
        if truth is None or truth.has(sp.Integral):
            return False, "sympy could not evaluate the integral"
        if sp.simplify(parsed - truth) == 0:
            return True, "OK (trusted/symbolic)"
        return False, f"not equal (sympy truth: {truth})"

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
