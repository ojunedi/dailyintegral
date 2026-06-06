"""
Verify candidate integral problems are correct AND gradeable by the app.

For each candidate:
  - INDEFINITE: integrate the integrand with SymPy, then confirm the stored
    `solution` LaTeX parses via the app's parse_latex_safely and is equivalent
    (up to a constant) to SymPy's antiderivative.
  - DEFINITE: evaluate the definite integral with SymPy, then confirm the stored
    `solution` LaTeX parses and equals that value exactly.

Only candidates that PASS both checks are safe to add. Run:
    uv run python -m migrations.verify_new_problems
"""
import sympy as sp

from app.utils import is_equivalent_up_to_constant, parse_latex_safely

x = sp.Symbol('x')

# Each candidate: key, integrand (sympy, in x), type, limits (for definite),
# solution LaTeX (what we'll store), difficulty, topic.
CANDIDATES = [
    # ---------- INDEFINITE ----------
    dict(key="x^2 ln x", integrand=x**2*sp.log(x), type="indefinite",
         sol=r"\frac{x^3}{3}\ln(x) - \frac{x^3}{9} + C", topic="Integration by Parts"),
    dict(key="x arctan x", integrand=x*sp.atan(x), type="indefinite",
         sol=r"\frac{x^2+1}{2}\arctan(x) - \frac{x}{2} + C", topic="Integration by Parts"),
    dict(key="(ln x)^2", integrand=sp.log(x)**2, type="indefinite",
         sol=r"x\ln(x)^2 - 2x\ln(x) + 2x + C", topic="Integration by Parts"),
    dict(key="arcsin x", integrand=sp.asin(x), type="indefinite",
         sol=r"x\arcsin(x) + \sqrt{1-x^2} + C", topic="Integration by Parts"),
    dict(key="sec^4 x", integrand=sp.sec(x)**4, type="indefinite",
         sol=r"\tan(x) + \frac{1}{3}\tan(x)^3 + C", topic="Trigonometric"),
    dict(key="x^2/(x^2+1)", integrand=x**2/(x**2+1), type="indefinite",
         sol=r"x - \arctan(x) + C", topic="Rational Functions"),
    dict(key="1/(x^2+2x+5)", integrand=1/(x**2+2*x+5), type="indefinite",
         sol=r"\frac{1}{2}\arctan\left(\frac{x+1}{2}\right) + C", topic="Completing the Square"),
    dict(key="(2x+3)/(x^2+1)", integrand=(2*x+3)/(x**2+1), type="indefinite",
         sol=r"\ln(x^2+1) + 3\arctan(x) + C", topic="Rational Functions"),
    dict(key="x^3 e^{x^2}", integrand=x**3*sp.exp(x**2), type="indefinite",
         sol=r"\frac{(x^2-1)e^{x^2}}{2} + C", topic="Substitution"),
    dict(key="ln x / x^2", integrand=sp.log(x)/x**2, type="indefinite",
         sol=r"-\frac{\ln(x)+1}{x} + C", topic="Integration by Parts"),
    dict(key="x cos 2x", integrand=x*sp.cos(2*x), type="indefinite",
         sol=r"\frac{x\sin(2x)}{2} + \frac{\cos(2x)}{4} + C", topic="Integration by Parts"),
    dict(key="sqrt(1-x^2)", integrand=sp.sqrt(1-x**2), type="indefinite",
         sol=r"\frac{x\sqrt{1-x^2} + \arcsin(x)}{2} + C", topic="Trigonometric Substitution"),
    dict(key="1/(1+e^x)", integrand=1/(1+sp.exp(x)), type="indefinite",
         sol=r"x - \ln(e^x + 1) + C", topic="Substitution"),
    dict(key="x sec^2 x", integrand=x*sp.sec(x)**2, type="indefinite",
         sol=r"x\tan(x) + \ln(\cos(x)) + C", topic="Integration by Parts"),
    dict(key="tan^3 x", integrand=sp.tan(x)**3, type="indefinite",
         sol=r"\frac{1}{2}\tan(x)^2 + \ln(\cos(x)) + C", topic="Trigonometric"),
    dict(key="e^{2x} sin x", integrand=sp.exp(2*x)*sp.sin(x), type="indefinite",
         sol=r"\frac{e^{2x}(2\sin(x)-\cos(x))}{5} + C", topic="Integration by Parts"),
    dict(key="1/(x^2-1)", integrand=1/(x**2-1), type="indefinite",
         sol=r"\frac{1}{2}\ln\left(\frac{x-1}{x+1}\right) + C", topic="Partial Fractions"),
    dict(key="x^2 cos x", integrand=x**2*sp.cos(x), type="indefinite",
         sol=r"x^2\sin(x) + 2x\cos(x) - 2\sin(x) + C", topic="Integration by Parts"),
    dict(key="x e^{-x}", integrand=x*sp.exp(-x), type="indefinite",
         sol=r"-(x+1)e^{-x} + C", topic="Integration by Parts"),
    dict(key="sin^3 x", integrand=sp.sin(x)**3, type="indefinite",
         sol=r"\frac{1}{3}\cos(x)^3 - \cos(x) + C", topic="Trigonometric"),
    dict(key="1/(x^2+4x+8)", integrand=1/(x**2+4*x+8), type="indefinite",
         sol=r"\frac{1}{2}\arctan\left(\frac{x+2}{2}\right) + C", topic="Completing the Square"),

    # ---------- DEFINITE ----------
    dict(key="int_0^{pi/2} sin^2", integrand=sp.sin(x)**2, type="definite", a=0, b=sp.pi/2,
         sol=r"\frac{\pi}{4}", topic="Definite"),
    dict(key="int_0^{pi/2} cos^4", integrand=sp.cos(x)**4, type="definite", a=0, b=sp.pi/2,
         sol=r"\frac{3\pi}{16}", topic="Definite"),
    dict(key="int_0^inf 1/(1+x^2)^2", integrand=1/(1+x**2)**2, type="definite", a=0, b=sp.oo,
         sol=r"\frac{\pi}{4}", topic="Improper Integral"),
    dict(key="int_0^inf e^{-x}cos x", integrand=sp.exp(-x)*sp.cos(x), type="definite", a=0, b=sp.oo,
         sol=r"\frac{1}{2}", topic="Improper Integral"),
    dict(key="int_0^{2pi} 1/(2+cos x)", integrand=1/(2+sp.cos(x)), type="definite", a=0, b=2*sp.pi,
         sol=r"\frac{2\pi}{\sqrt{3}}", topic="Definite"),
    dict(key="int_0^{pi/2} sin^4", integrand=sp.sin(x)**4, type="definite", a=0, b=sp.pi/2,
         sol=r"\frac{3\pi}{16}", topic="Definite"),
    # dict(key="int_0^1 ln(1+x)/(1+x^2)", integrand=sp.log(1+x)/(1+x**2), type="definite", a=0, b=1,
    #      sol=r"\frac{\pi\ln(2)}{8}", topic="Competition"),
    dict(key="int_0^{pi} x sin x", integrand=x*sp.sin(x), type="definite", a=0, b=sp.pi,
         sol=r"\pi", topic="Definite"),
    dict(key="int_0^inf x^2 e^{-x}", integrand=x**2*sp.exp(-x), type="definite", a=0, b=sp.oo,
         sol=r"2", topic="Improper Integral"),
]


def check(c):
    is_indef = c["type"] == "indefinite"
    parsed = parse_latex_safely(c["sol"], is_indefinite=is_indef)
    if parsed is None:
        return False, "solution LaTeX did NOT parse"
    # parse_latex renders `e` and `\pi` as plain symbols. The APP is self-consistent
    # (it compares two parse_latex outputs, never sympy.integrate), so this is fine
    # for grading. But to verify correctness against sympy's integrate() we normalize
    # those symbols to the real constants E / pi here.
    parsed = parsed.subs({sp.Symbol('e'): sp.E, sp.Symbol('pi'): sp.pi})
    try:
        if is_indef:
            truth = sp.integrate(c["integrand"], x)
        else:
            truth = sp.integrate(c["integrand"], (x, c["a"], c["b"]))
    except Exception as e:
        return False, f"sympy integrate failed: {e}"
    if truth is None or truth.has(sp.Integral):
        return False, "sympy could not evaluate the integral"
    ok = is_equivalent_up_to_constant(parsed, truth, is_indefinite=is_indef)
    return ok, ("OK" if ok else f"NOT equivalent (sympy truth: {truth})")


def main():
    passed, failed = [], []
    for c in CANDIDATES:
        ok, msg = check(c)
        tag = "PASS" if ok else "FAIL"
        (passed if ok else failed).append(c["key"])
        print(f"[{tag}] {c['type']:10s} {c['key']:28s} {msg}")
    print(f"\n{len(passed)} passed, {len(failed)} failed")
    if failed:
        print("FAILED:", failed)


if __name__ == "__main__":
    main()
