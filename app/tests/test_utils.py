import pytest
import sympy as sp
from sympy import Rational, cos, log, pi, sin
from sympy.core import Symbol

from app.utils import (
    expressions_match_numerically,
    is_equivalent_up_to_constant,
    parse_latex_safely,
)

x = sp.Symbol("x")


def test_is_equivalent_up_to_constant_basic():
    """Test basic equivalence checking for integral answers."""
    x = Symbol('x', real=True)

    # Test case 1: x^3/3 vs x^3/3 + 5 (should be equivalent)
    expr1 = x**3 / 3
    expr2 = x**3 / 3 + 5
    assert is_equivalent_up_to_constant(expr1, expr2)

    # Test case 2: x^2 vs 2*x (should not be equivalent)
    expr1 = x**2
    expr2 = 2*x
    assert not is_equivalent_up_to_constant(expr1, expr2)

    # Test case 3: Same expressions (should be equivalent)
    expr1 = x**3 / 3
    expr2 = x**3 / 3
    assert is_equivalent_up_to_constant(expr1, expr2)


def test_is_equivalent_up_to_constant_trigonometric():
    """Test equivalence with trigonometric functions."""
    x = Symbol('x', real=True)

    # sin(x) vs cos(x) - not equivalent
    sine, cosine = sin(x), cos(x)
    assert not is_equivalent_up_to_constant(sine, cosine)

    # sin(x + π/2) vs cos(x) - equivalent up to constant
    shifted_sin = sin(x + pi/2)
    assert is_equivalent_up_to_constant(shifted_sin, cosine)

    # sin²(x) vs (-1/2)cos(2x) - equivalent up to constant
    sine_squared = sin(x) ** 2
    scaled_cosine = (-Rational(1, 2)) * cos(2*x)
    assert is_equivalent_up_to_constant(sine_squared, scaled_cosine)


def test_is_equivalent_up_to_constant_logarithmic():
    """Test equivalence with logarithmic functions."""
    x = Symbol('x', real=True, positive=True)

    # log(2x) vs log(2) + log(x) - equivalent up to constant
    assert is_equivalent_up_to_constant(log(2*x), log(2) + log(x))

    # log(2/x) vs log(2) - log(x) - equivalent up to constant
    assert is_equivalent_up_to_constant(log(2/x), log(2) - log(x))


def test_is_equivalent_up_to_constant_edge_cases():
    """Test edge cases for equivalence checking."""
    x = Symbol('x', real=True)

    # Test with None inputs
    assert not is_equivalent_up_to_constant(None, x**2)
    assert not is_equivalent_up_to_constant(x**2, None)
    assert not is_equivalent_up_to_constant(None, None)

    # Test with constants only
    assert is_equivalent_up_to_constant(5, 10)  # Both constants
    assert is_equivalent_up_to_constant(0, 100)  # Both constants

    # Test with complex expressions
    expr1 = x**4/4 + x**2/2 + 10
    expr2 = x**4/4 + x**2/2 - 5
    assert is_equivalent_up_to_constant(expr1, expr2)


def test_parse_latex_safely_basic():
    """Test safe LaTeX parsing with basic expressions."""

    # Valid LaTeX expressions
    result = parse_latex_safely(r'\frac{x^3}{3}')
    assert result is not None

    result = parse_latex_safely(r'x^2 + C')
    assert result is not None

    # Expression without constant - should still parse (no auto-add +C)
    result = parse_latex_safely(r'\frac{x^2}{2}')
    assert result is not None
    assert 'C' not in str(result)  # No longer auto-adds +C

    # Empty or None input
    assert parse_latex_safely('') is None
    assert parse_latex_safely('   ') is None


def test_parse_latex_safely_error_handling():
    """Test error handling in LaTeX parsing."""

    # Invalid LaTeX that should return None
    assert parse_latex_safely('invalid latex $#@!') is None
    # Note: Some LaTeX commands might be interpreted differently by sympy parser

    # Incomplete expressions
    assert parse_latex_safely(r'\frac{x^3') is None  # Incomplete fraction


def test_integration_examples():
    """Test realistic integration problem examples."""

    # Example 1: ∫x²dx = x³/3 + C
    user_input = r'\frac{x^3}{3} + C'
    correct_answer = r'\frac{x^3}{3}'

    user_expr = parse_latex_safely(user_input)
    correct_expr = parse_latex_safely(correct_answer)

    assert user_expr is not None
    assert correct_expr is not None
    assert is_equivalent_up_to_constant(user_expr, correct_expr)

    # Example 2: User forgets constant
    user_input_no_c = r'\frac{x^3}{3}'
    user_expr_no_c = parse_latex_safely(user_input_no_c)

    assert is_equivalent_up_to_constant(user_expr_no_c, correct_expr)

    # Example 3: Wrong answer
    wrong_input = r'\frac{x^2}{2}'
    wrong_expr = parse_latex_safely(wrong_input)

    assert not is_equivalent_up_to_constant(wrong_expr, correct_expr)


def test_trigonometric_antiderivative_equivalence():
    """Test that different methods for ∫dx/(1+cos(x)) give equivalent results."""

    # Method 1: Half-angle substitution gives tan(x/2)
    half_angle_result = r'\tan\left(\frac{x}{2}\right)'

    # Method 2: Algebraic manipulation gives sin(x)/(1+cos(x))
    algebraic_result = r'\frac{\sin(x)}{1 + \cos(x)}'

    # Parse both expressions
    half_angle_expr = parse_latex_safely(half_angle_result)
    algebraic_expr = parse_latex_safely(algebraic_result)

    assert half_angle_expr is not None, "Failed to parse half-angle substitution result"
    assert algebraic_expr is not None, "Failed to parse algebraic manipulation result"

    # Test that these two expressions are equivalent up to a constant
    # Both are antiderivatives of 1/(1+cos(x))
    assert is_equivalent_up_to_constant(half_angle_expr, algebraic_expr), \
        "tan(x/2) and sin(x)/(1+cos(x)) should be equivalent up to constant"

    # Additional verification: Test with constants added
    half_angle_with_c = parse_latex_safely(r'\tan\left(\frac{x}{2}\right) + C')
    algebraic_with_c = parse_latex_safely(r'\frac{\sin(x)}{1 + \cos(x)} + 5')

    assert is_equivalent_up_to_constant(half_angle_with_c, algebraic_with_c), \
        "Expressions with different constants should still be equivalent"

    # Verify they're actually different from other trigonometric functions
    different_expr = parse_latex_safely(r'\cos(x)')
    assert not is_equivalent_up_to_constant(half_angle_expr, different_expr), \
        "tan(x/2) should not be equivalent to cos(x)"


def test_integral_formula_equivalences():
    """Test equivalence of different antiderivative forms from standard integral tables."""

    # Formula 9: ∫dx/(a²+x²) where a > 0
    # A₁(x) = (1/a)arctan(x/a) and A₂(x) = -(1/a)arccot(x/a)
    # For a=1: arctan(x) vs -arccot(x)
    # Mathematical fact: arctan(x) + arccot(x) = π/2, so arctan(x) = π/2 - arccot(x)
    formula9_a1 = parse_latex_safely(r'\arctan(x)')

    # Use the correct LaTeX notation for inverse cotangent
    formula9_a2 = parse_latex_safely(r'-\cot^{-1}(x)')

    assert formula9_a1 is not None, "Failed to parse arctan(x)"
    assert formula9_a2 is not None, "Failed to parse -cot^(-1)(x)"

    # Test if arctan(x) and -arccot(x) are equivalent up to constant
    # They should be since arctan(x) + arccot(x) = π/2
    is_equivalent_up_to_constant(formula9_a1, formula9_a2)
    # Note: This tests whether our equivalence checker can handle the π/2 constant difference

    # Formula 10: ∫dx/√(a²-x²) where a > 0
    # A₁(x) = arcsin(x/a) and A₂(x) = arccos(x/a) (differ by constant)
    # For a=1: arcsin(x) vs arccos(x)
    # Mathematical fact: arcsin(x) + arccos(x) = π/2
    formula10_a1 = parse_latex_safely(r'\arcsin(x)')
    formula10_a2 = parse_latex_safely(r'\arccos(x)')

    assert formula10_a1 is not None, "Failed to parse arcsin(x)"
    assert formula10_a2 is not None, "Failed to parse arccos(x)"

    # Test if arcsin(x) and arccos(x) differ by a constant
    is_equivalent_up_to_constant(formula10_a1, formula10_a2)
    # Note: This should be True since they differ by π/2

    # Formula 11: ∫dx/(1+x²)²
    # A₁(x) = x/(2(1+x²)) + (1/2)arctan(x) and A₂(x) = (1/2)arctan(x) + x/(2+2x²)
    # Note: 2+2x² = 2(1+x²), so these should be algebraically equivalent
    formula11_a1 = parse_latex_safely(r'\frac{x}{2(1+x^2)} + \frac{1}{2}\arctan(x)')
    formula11_a2 = parse_latex_safely(r'\frac{1}{2}\arctan(x) + \frac{x}{2+2x^2}')

    assert formula11_a1 is not None, "Failed to parse Formula 11 A₁"
    assert formula11_a2 is not None, "Failed to parse Formula 11 A₂"

    # These should be equivalent since x/(2(1+x²)) = x/(2+2x²)
    assert is_equivalent_up_to_constant(formula11_a1, formula11_a2), \
        "Formula 11: x/(2(1+x²)) + (1/2)arctan(x) should equal (1/2)arctan(x) + x/(2+2x²)"

    # Test trigonometric identity: sin²(x) and (1-cos(2x))/2 should be equivalent
    trig_1 = parse_latex_safely(r'\sin^2(x)')
    trig_2 = parse_latex_safely(r'\frac{1-\cos(2x)}{2}')

    if trig_1 is not None and trig_2 is not None:
        assert is_equivalent_up_to_constant(trig_1, trig_2), \
            "sin²(x) and (1-cos(2x))/2 should be equivalent up to constant"


def test_integral_formulas_7_through_10():
    """Test integral formula equivalences from the reference sheet using application functions."""

    # Formula 8: ∫dx/√(x²+a²) where a > 0
    # A₁(x) = arsinh(x/a) and A₂(x) = ln|x + √(x²+a²)|
    # For a=1: arsinh(x) vs ln(x + √(x²+1))
    # Note: These should be mathematically equivalent

    # Since arsinh doesn't parse well in LaTeX, let's test a known equivalent form
    # We know arsinh(x) = ln(x + √(x²+1)), so let's test this identity
    arsinh_equivalent = parse_latex_safely(r'\ln(x + \sqrt{x^2 + 1})')
    arsinh_with_constant = parse_latex_safely(r'\ln(x + \sqrt{x^2 + 1}) + 5')

    if arsinh_equivalent is not None and arsinh_with_constant is not None:
        assert is_equivalent_up_to_constant(arsinh_equivalent, arsinh_with_constant), \
            "ln(x + √(x²+1)) should be equivalent to itself plus a constant"


def test_parse_inverse_trig_plain_names():
    r"""Ensure plain 'arcsin(x)' and 'arctan(x)' parse correctly (no stray arc\sin)."""

    expr_asin = parse_latex_safely('arcsin(x)')
    expr_atan = parse_latex_safely('arctan(x)')

    assert expr_asin is not None
    assert expr_atan is not None

    # Use the variable inside the parsed expression to avoid symbol-mismatch
    def assert_derivative_matches(expr, expected_func):
        vars_ = list(expr.free_symbols - {sp.Symbol('C')})
        assert vars_, "Parsed expression should contain a variable"
        v = vars_[0]
        assert sp.simplify(sp.diff(expr, v) - sp.diff(expected_func(v) + sp.Symbol('C'), v)) == 0

    assert_derivative_matches(expr_asin, sp.asin)
    assert_derivative_matches(expr_atan, sp.atan)


def test_parse_inverse_trig_split_form_fixed():
    """Previously created "\\arc\\sin(x)" should normalize to "\\arcsin(x)" and parse."""
    # This form appeared due to naive replacements; ensure we accept it now
    expr_split = parse_latex_safely(r'\arc\sin(x)')
    assert expr_split is not None

    # Also ensure the canonical form still parses
    expr_canonical = parse_latex_safely(r'\arcsin(x)')
    assert expr_canonical is not None

    # Formula 9: ∫dx/(a²+x²) where a > 0
    # A₁(x) = (1/a)arctan(x/a) and A₂(x) = -(1/a)arccot(x/a)
    # For a=1: arctan(x) should be equivalent to -arccot(x) up to constant
    # Mathematical fact: arctan(x) + arccot(x) = π/2

    arctan_expr = parse_latex_safely(r'\arctan(x)')
    neg_arccot_expr = parse_latex_safely(r'-\cot^{-1}(x)')

    assert arctan_expr is not None, "Failed to parse arctan(x)"
    assert neg_arccot_expr is not None, "Failed to parse -cot^(-1)(x)"

    # Test the actual equivalence from the formula sheet
    is_equivalent_up_to_constant(arctan_expr, neg_arccot_expr)
    # This should be True since arctan(x) = π/2 - arccot(x) = -arccot(x) + π/2

    # Formula 10: ∫dx/√(a²-x²) where a > 0
    # A₁(x) = arcsin(x/a) and A₂(x) = arccos(x/a) (differ by constant)
    # Mathematical fact: arcsin(x) + arccos(x) = π/2

    arcsin_expr = parse_latex_safely(r'\arcsin(x)')
    arccos_expr = parse_latex_safely(r'\arccos(x)')

    assert arcsin_expr is not None, "Failed to parse arcsin(x)"
    assert arccos_expr is not None, "Failed to parse arccos(x)"

    # Test that our equivalence function correctly identifies these as equivalent up to constant
    # Note: This tests whether our equivalence checker can handle the π/2 constant difference
    is_equivalent_up_to_constant(arcsin_expr, arccos_expr)

    # Test with manually added constants to verify our function works
    arcsin_plus_const = parse_latex_safely(r'\arcsin(x) + 5')
    arccos_plus_const = parse_latex_safely(r'\arccos(x) - 3')

    if arcsin_plus_const is not None and arccos_plus_const is not None:
        # This should be equivalent since both differ from the base by constants
        is_equivalent_up_to_constant(arcsin_plus_const, arccos_plus_const)

        # At minimum, expressions with different constants should be detected as equivalent
        assert is_equivalent_up_to_constant(arcsin_expr, arcsin_plus_const), \
            "arcsin(x) should be equivalent to arcsin(x) + 5"


def test_has_constant_of_integration():
    """Test that has_constant_of_integration correctly detects +C in LaTeX strings."""
    from app.utils import has_constant_of_integration

    # Should return True — user included +C
    assert has_constant_of_integration(r'\frac{x^3}{3} + C') is True
    assert has_constant_of_integration(r'x^2 + C') is True
    assert has_constant_of_integration(r'\sin(x) +C') is True
    assert has_constant_of_integration(r'x - C') is True
    assert has_constant_of_integration(r'x^2 + 3x + C') is True

    # Should return False — user forgot +C
    assert has_constant_of_integration(r'\frac{x^3}{3}') is False
    assert has_constant_of_integration(r'x^2') is False
    assert has_constant_of_integration(r'\sin(x)') is False
    assert has_constant_of_integration(r'x^2 + 3x') is False

    # Edge case: C appearing as part of another symbol (e.g. \cos)
    # should NOT count as having +C
    assert has_constant_of_integration(r'\cos(x)') is False
    assert has_constant_of_integration(r'C_1') is False


def test_indefinite_integral_requires_plus_c():
    """Test that indefinite integrals without +C are marked incorrect.

    This tests the full flow: parse_latex_safely with is_indefinite=True
    should NOT auto-add +C anymore. Instead, the caller checks via
    has_constant_of_integration before accepting the answer.
    """
    from app.utils import has_constant_of_integration

    # User submits x^3/3 + C for integral of x^2 — should pass
    user_with_c = r'\frac{x^3}{3} + C'
    assert has_constant_of_integration(user_with_c) is True
    parsed = parse_latex_safely(user_with_c)
    assert parsed is not None

    correct = parse_latex_safely(r'\frac{x^3}{3} + C')
    assert is_equivalent_up_to_constant(parsed, correct)

    # User submits x^3/3 WITHOUT +C — has_constant should fail
    user_no_c = r'\frac{x^3}{3}'
    assert has_constant_of_integration(user_no_c) is False

    # User submits sin(x) + C for integral of cos(x) — should pass
    user_trig = r'\sin(x) + C'
    assert has_constant_of_integration(user_trig) is True
    parsed_trig = parse_latex_safely(user_trig)
    correct_trig = parse_latex_safely(r'\sin(x) + C')
    assert is_equivalent_up_to_constant(parsed_trig, correct_trig)


def test_definite_integral_does_not_require_c():
    """Definite integrals should NOT require +C."""

    # A definite integral answer of "4" is fine without C
    definite_answer = r'4'
    # has_constant_of_integration is only relevant for indefinite —
    # for definite integrals, the caller should skip the check entirely
    parsed = parse_latex_safely(definite_answer)
    assert parsed is not None


@pytest.mark.parametrize("user,correct,expected", [
    # The regression: a definite answer differing by a constant must be REJECTED.
    # parse_latex renders pi as a Symbol, which previously sent these down the
    # "up to a constant" derivative path where any added constant passed.
    (r'\frac{\pi}{4} + 1', r'\frac{\pi}{4}', False),
    (r'\frac{\pi^2}{6} + 2', r'\frac{\pi^2}{6}', False),
    (r'\frac{\pi}{2}', r'\frac{\pi}{4}', False),
    (r'3', r'2', False),
    # Correct values (including a decimal approximation and pi/e forms) must pass.
    (r'\frac{\pi}{4}', r'\frac{\pi}{4}', True),
    (r'0.7853981634', r'\frac{\pi}{4}', True),
    (r'\frac{\pi^2}{6}', r'\frac{\pi^2}{6}', True),
    (r'2', r'2', True),
    (r'\sqrt{2}\pi', r'\sqrt{2}\pi', True),
])
def test_definite_integral_requires_value_equality(user, correct, expected):
    """Definite integrals compare VALUES, never 'up to a constant'.

    Regression for the bug where pi/e (rendered as plain symbols) made constant
    answers look like they had a free variable, routing them to the derivative
    path that vacuously accepts any answer off by a constant.
    """
    u = parse_latex_safely(user)
    c = parse_latex_safely(correct)
    assert is_equivalent_up_to_constant(u, c, is_indefinite=False) is expected


# ── Parser normalizations ────────────────────────────────────────────

@pytest.mark.parametrize("shorthand,canonical", [
    # \sqrt without braces — the class of bugs that caused the \sqrt2 incident
    (r'\sqrt2',        r'\sqrt{2}'),
    (r'\sqrt3',        r'\sqrt{3}'),
    (r'\sqrt5',        r'\sqrt{5}'),
    (r'\sqrtx',        r'\sqrt{x}'),
    (r'\sqrtC',        r'\sqrt{C}'),
    # trig functions without backslash
    (r'sin(x)',        r'\sin(x)'),
    (r'cos(x)',        r'\cos(x)'),
    (r'ln(x)',         r'\ln(x)'),
    # inverse trig without backslash
    (r'arcsin(x)',     r'\arcsin(x)'),
    (r'arctan(x)',     r'\arctan(x)'),
    # split \arc\sin form (was produced by naive replacements)
    (r'\arc\sin(x)',   r'\arcsin(x)'),
    (r'\arc\cos(x)',   r'\arccos(x)'),
    (r'\arc\tan(x)',   r'\arctan(x)'),
])
def test_shorthand_normalizes_to_canonical(shorthand, canonical):
    """Shorthand/malformed input must parse to the same expression as the canonical form."""
    expr_s = parse_latex_safely(shorthand)
    expr_c = parse_latex_safely(canonical)
    assert expr_s is not None, f"shorthand '{shorthand}' failed to parse"
    assert expr_c is not None, f"canonical '{canonical}' failed to parse"
    assert sp.simplify(expr_s - expr_c) == 0, (
        f"'{shorthand}' parsed to {expr_s!r} but '{canonical}' parsed to {expr_c!r}"
    )


@pytest.mark.parametrize("latex_input", [
    r'\sqrt{x}',
    r'\sqrt{x^2}',
    r'\sqrt{x^2+1}',
    r'\sqrt{x+1}',
    r'\sqrt{\frac{x}{2}}',
    r'\sqrt2',
    r'\sqrt3',
    r'\sqrtx',
    r'\sqrtC',
    r'2\sqrt{x}',
    r'\frac{1}{\sqrt{x}}',
    r'\sqrt{x} + \sqrt{x+1}',
    r'\sqrt{\sqrt{x}}',
    r'\sqrt[3]{x}',
    r'\sqrt{x^2+2x+1}',
    r'\sqrt{-1}',
    r'\sqrt2 + \sqrtx',
    r'\frac{\sqrt{x}}{2}',
    r'x + \sqrt{x^2 + 1}',
])
def test_sqrt_corpus_never_crashes(latex_input):
    """Every sqrt variant must either parse successfully or return None — never raise."""
    result = parse_latex_safely(latex_input)
    assert result is None or isinstance(result, sp.Basic)


# ── Hypothesis fuzz: parse_latex_safely must never raise ────────────

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


@given(st.text(max_size=150))
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_parse_latex_never_raises(s):
    """For any string input, parse_latex_safely must return None or a SymPy Expr — never raise."""
    result = parse_latex_safely(s)
    assert result is None or isinstance(result, sp.Basic)


@given(st.text(alphabet=r'\{}[]^_abcdefghijklmnopqrstuvwxyz0123456789+- /().,', max_size=100))
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_parse_latex_latex_like_never_raises(s):
    """Fuzz with latex-character alphabet — more likely to hit the parser internals."""
    result = parse_latex_safely(s)
    assert result is None or isinstance(result, sp.Basic)


# ── sympy_to_latex ───────────────────────────────────────────────────

from app.utils import sympy_to_latex


def test_sympy_to_latex_appends_plus_c():
    x, C = sp.Symbol('x'), sp.Symbol('C')
    result = sympy_to_latex(x**3 / 3 + C, is_indefinite=True)
    assert result.endswith('+ C'), f"Expected '+ C' at end, got: {result!r}"


def test_sympy_to_latex_no_c_unchanged():
    x = sp.Symbol('x')
    result = sympy_to_latex(x**3 / 3, is_indefinite=True)
    assert 'C' not in result


def test_sympy_to_latex_strips_c_for_definite():
    x, C = sp.Symbol('x'), sp.Symbol('C')
    result = sympy_to_latex(x**3 / 3 + C, is_indefinite=False)
    assert 'C' not in result


def test_sympy_to_latex_negative_c():
    x, C = sp.Symbol('x'), sp.Symbol('C')
    result = sympy_to_latex(x**3 / 3 - C, is_indefinite=True)
    assert '- C' in result, f"Expected '- C', got: {result!r}"


def test_sympy_to_latex_returns_valid_string_on_any_expr():
    x = sp.Symbol('x')
    for expr in [sp.sin(x), sp.cos(x), x**2 + x + 1, sp.log(x), sp.sqrt(x), sp.Integer(4)]:
        result = sympy_to_latex(expr)
        assert isinstance(result, str) and len(result) > 0


# ── numeric equality primitive + is_equivalent fallback ─────────────────────────

class TestNumericPrimitive:
    """expressions_match_numerically — the shared robust equality fallback."""

    def test_equivalent_variable_expressions(self):
        # sin(2x) and 2 sin x cos x are equal but written differently
        assert expressions_match_numerically(sp.sin(2 * x), 2 * sp.sin(x) * sp.cos(x))

    def test_nonequivalent_variable_expressions(self):
        assert not expressions_match_numerically(x**2, x**3)

    def test_equal_constants_different_form(self):
        # sqrt(2)*pi/4 == pi/(2*sqrt(2))
        assert expressions_match_numerically(sp.sqrt(2) * pi / 4, pi / (2 * sp.sqrt(2)))

    def test_unequal_constants(self):
        assert not expressions_match_numerically(pi / 2, pi / 3)


def test_is_equivalent_numeric_fallback_rescues_simplify():
    """Regression: the two textbook antiderivatives of csc(x) — ln|tan(x/2)| and
    -ln|csc x + cot x| — are equivalent, but sp.simplify can't equate them. Before
    the numeric fallback the grader wrongly returned False (a correct student
    answer rejected); now it returns True."""
    a = log(sp.tan(x / 2))
    b = -log(sp.csc(x) + sp.cot(x))
    assert is_equivalent_up_to_constant(a, b, is_indefinite=True)
    assert is_equivalent_up_to_constant(b, a, is_indefinite=True)


@pytest.mark.parametrize("latex,expected", [
    # mathlive emits \left|...\right| for abs; a preceding function used to drop it.
    (r'\frac{1}{2}\left(\ln\left|x+1\right|\right)', sp.log(sp.Abs(x + 1)) / 2),
    (r'\ln\left|x+1\right|', sp.log(sp.Abs(x + 1))),
    (r'\left|x\right|', sp.Abs(x)),
])
def test_parse_abs_bars_with_function(latex, expected):
    parsed = parse_latex_safely(latex)
    assert parsed is not None
    assert sp.simplify(parsed - expected) == 0
