"""
Problem registry — the canonical source of truth for all problems managed
through this scaffolding.

To add a problem: append a NewProblem(...) entry to PROBLEMS, then run:
    uv run python -m migrations.add_problems

The runner verifies every entry against SymPy before uploading anything.
If any entry fails verification, nothing is uploaded.

To update an existing problem (e.g. fix a hint, add a missing difficulty):
edit the entry here and re-run the runner — it matches on problem text and
updates all fields in place.

To verify without uploading:
    uv run python -m migrations.add_problems --check
"""
import sympy as sp

from migrations.problem_models import NewProblem

x = sp.Symbol("x")

PROBLEMS: list[NewProblem] = [
    # ── Integration by Parts ──────────────────────────────────────────────────
    NewProblem(
        problem=r"\int x^2 \ln(x) dx",
        solution=r"\frac{x^3}{3}\ln(x) - \frac{x^3}{9} + C",
        integrand=x**2 * sp.log(x),
        topic="Integration by Parts",
        difficulty="medium",
        progressive_hints=[
            r"Use integration by parts: $\int u \, dv = uv - \int v \, du$",
            r"Let $u = \ln(x)$ and $dv = x^2 dx$",
            r"Then $du = \frac{1}{x}dx$ and $v = \frac{x^3}{3}$; the leftover integral is elementary",
        ],
    ),
    NewProblem(
        problem=r"\int x \arctan(x) dx",
        solution=r"\frac{x^2+1}{2}\arctan(x) - \frac{x}{2} + C",
        integrand=x * sp.atan(x),
        topic="Integration by Parts",
        difficulty="medium",
        progressive_hints=[
            r"Let $u = \arctan(x)$, $dv = x \, dx$",
            r"Then $du = \frac{1}{1+x^2}dx$ and $v = \frac{x^2}{2}$",
            r"The remaining $\int \frac{x^2}{2(1+x^2)}dx$ simplifies via $\frac{x^2}{1+x^2} = 1 - \frac{1}{1+x^2}$",
        ],
    ),
    NewProblem(
        problem=r"\int \ln^2(x) dx",
        solution=r"x\ln(x)^2 - 2x\ln(x) + 2x + C",
        integrand=sp.log(x)**2,
        topic="Integration by Parts",
        difficulty="hard",
        progressive_hints=[
            r"Let $u = \ln^2(x)$ and $dv = dx$, so $v = x$",
            r"This leaves $\int 2\ln(x) dx$ — apply parts again",
            r"Recall $\int \ln(x) dx = x\ln(x) - x$",
        ],
    ),
    NewProblem(
        problem=r"\int \arcsin(x) dx",
        solution=r"x\arcsin(x) + \sqrt{1-x^2} + C",
        integrand=sp.asin(x),
        topic="Integration by Parts",
        difficulty="medium",
        progressive_hints=[
            r"Let $u = \arcsin(x)$ and $dv = dx$",
            r"Then $du = \frac{1}{\sqrt{1-x^2}}dx$ and $v = x$",
            r"The leftover $\int \frac{x}{\sqrt{1-x^2}}dx$ yields $-\sqrt{1-x^2}$ by substitution",
        ],
    ),
    NewProblem(
        problem=r"\int x \sec^2(x) dx",
        solution=r"x\tan(x) + \ln(\cos(x)) + C",
        integrand=x * sp.sec(x)**2,
        topic="Integration by Parts",
        difficulty="medium",
        progressive_hints=[
            r"Let $u = x$ and $dv = \sec^2(x)dx$, so $v = \tan(x)$",
            r"This leaves $\int \tan(x) dx$",
            r"Recall $\int \tan(x) dx = -\ln|\cos(x)|$",
        ],
    ),
    NewProblem(
        problem=r"\int x^2 \cos(x) dx",
        solution=r"x^2\sin(x) + 2x\cos(x) - 2\sin(x) + C",
        integrand=x**2 * sp.cos(x),
        topic="Integration by Parts",
        difficulty="medium",
        progressive_hints=[
            r"Let $u = x^2$, $dv = \cos(x)dx$",
            r"After one application you get $\int 2x\sin(x)dx$ — apply parts again",
            r"Each step lowers the power of $x$ by one until it vanishes",
        ],
    ),

    # ── Trigonometric ─────────────────────────────────────────────────────────
    NewProblem(
        problem=r"\int \sec^4(x) dx",
        solution=r"\tan(x) + \frac{1}{3}\tan(x)^3 + C",
        integrand=sp.sec(x)**4,
        topic="Trigonometric",
        difficulty="medium",
        progressive_hints=[
            r"Write $\sec^4(x) = \sec^2(x)\cdot\sec^2(x)$",
            r"Replace one factor: $\sec^2(x) = 1 + \tan^2(x)$",
            r"Substitute $u = \tan(x)$, $du = \sec^2(x)dx$, then integrate $1 + u^2$",
        ],
    ),
    NewProblem(
        problem=r"\int \tan^3(x) dx",
        solution=r"\frac{1}{2}\tan(x)^2 + \ln(\cos(x)) + C",
        integrand=sp.tan(x)**3,
        topic="Trigonometric",
        difficulty="medium",
        progressive_hints=[
            r"Write $\tan^3(x) = \tan(x)(\sec^2(x) - 1)$",
            r"Split into $\int \tan(x)\sec^2(x)dx - \int \tan(x)dx$",
            r"The first is $\frac{1}{2}\tan^2(x)$ by $u=\tan x$; the second is $\ln|\cos x|$",
        ],
    ),
    NewProblem(
        problem=r"\int \sin^3(x) dx",
        solution=r"\frac{1}{3}\cos(x)^3 - \cos(x) + C",
        integrand=sp.sin(x)**3,
        topic="Trigonometric",
        difficulty="easy",
        progressive_hints=[
            r"Write $\sin^3(x) = \sin(x)(1 - \cos^2(x))$",
            r"Substitute $u = \cos(x)$, $du = -\sin(x)dx$",
            r"Integrate $-(1 - u^2)$ in $u$",
        ],
    ),

    # ── Trigonometric Substitution ────────────────────────────────────────────
    NewProblem(
        problem=r"\int \sqrt{1-x^2} dx",
        solution=r"\frac{x\sqrt{1-x^2} + \arcsin(x)}{2} + C",
        integrand=sp.sqrt(1 - x**2),
        topic="Trigonometric Substitution",
        difficulty="hard",
        progressive_hints=[
            r"Let $x = \sin(\theta)$, so $\sqrt{1-x^2} = \cos(\theta)$ and $dx = \cos(\theta)d\theta$",
            r"The integral becomes $\int \cos^2(\theta) d\theta$",
            r"Use $\cos^2(\theta) = \frac{1+\cos(2\theta)}{2}$, then convert back to $x$",
        ],
    ),

    # ── Partial Fractions ─────────────────────────────────────────────────────
    NewProblem(
        problem=r"\int \frac{1}{x^2-1} dx",
        solution=r"\frac{1}{2}\ln\left(\frac{x-1}{x+1}\right) + C",
        integrand=1 / (x**2 - 1),
        topic="Partial Fractions",
        difficulty="medium",
        progressive_hints=[
            r"Factor: $\frac{1}{x^2-1} = \frac{1}{(x-1)(x+1)}$",
            r"Decompose: $\frac{1}{(x-1)(x+1)} = \frac{1/2}{x-1} - \frac{1/2}{x+1}$",
            r"Integrate each term to logarithms and combine",
        ],
    ),

    # ── Completing the Square ─────────────────────────────────────────────────
    NewProblem(
        problem=r"\int \frac{1}{x^2+2x+5} dx",
        solution=r"\frac{1}{2}\arctan\left(\frac{x+1}{2}\right) + C",
        integrand=1 / (x**2 + 2*x + 5),
        topic="Completing the Square",
        difficulty="medium",
        progressive_hints=[
            r"Complete the square: $x^2+2x+5 = (x+1)^2 + 4$",
            r"Use the form $\int \frac{1}{u^2 + a^2}du = \frac{1}{a}\arctan\left(\frac{u}{a}\right)$",
            r"Here $u = x+1$ and $a = 2$",
        ],
    ),

    # ── Substitution ──────────────────────────────────────────────────────────
    NewProblem(
        problem=r"\int x^3 e^{x^2} dx",
        solution=r"\frac{(x^2-1)e^{x^2}}{2} + C",
        integrand=x**3 * sp.exp(x**2),
        topic="Substitution",
        difficulty="hard",
        progressive_hints=[
            r"Let $u = x^2$, $du = 2x \, dx$; note $x^3 dx = x^2 \cdot x \, dx = \frac{u}{2}du$",
            r"The integral becomes $\frac{1}{2}\int u e^u du$",
            r"Integrate $u e^u$ by parts: $u e^u - e^u$, then back-substitute",
        ],
    ),
    NewProblem(
        problem=r"\int \frac{1}{1+e^x} dx",
        solution=r"x - \ln(e^x + 1) + C",
        integrand=1 / (1 + sp.exp(x)),
        topic="Substitution",
        difficulty="medium",
        progressive_hints=[
            r"Multiply through or split: $\frac{1}{1+e^x} = 1 - \frac{e^x}{1+e^x}$",
            r"The first term integrates to $x$",
            r"For the second, substitute $u = 1+e^x$, $du = e^x dx$, giving $-\ln(1+e^x)$",
        ],
    ),

    # ── Definite ──────────────────────────────────────────────────────────────
    NewProblem(
        problem=r"\int_0^{\pi/2} \sin^2(x) dx",
        solution=r"\frac{\pi}{4}",
        integrand=sp.sin(x)**2,
        integral_type="definite",
        lower=sp.Integer(0),
        upper=sp.pi / 2,
        topic="Definite Trigonometric",
        difficulty="easy",
        progressive_hints=[
            r"Use $\sin^2(x) = \frac{1 - \cos(2x)}{2}$",
            r"Integrate term by term over $[0, \pi/2]$",
            r"The $\cos(2x)$ term integrates to $0$ over this interval",
        ],
    ),
    NewProblem(
        problem=r"\int_0^{\pi/2} \cos^4(x) dx",
        solution=r"\frac{3\pi}{16}",
        integrand=sp.cos(x)**4,
        integral_type="definite",
        lower=sp.Integer(0),
        upper=sp.pi / 2,
        topic="Definite Trigonometric",
        difficulty="hard",
        progressive_hints=[
            r"Use $\cos^2(x) = \frac{1+\cos(2x)}{2}$, then square it",
            r"Expand and apply the half-angle identity again to $\cos^2(2x)$",
            r"Alternatively use the Wallis formula for $\int_0^{\pi/2}\cos^n$",
        ],
    ),
    NewProblem(
        problem=r"\int_0^{\infty} \frac{1}{(1+x^2)^2} dx",
        solution=r"\frac{\pi}{4}",
        integrand=1 / (1 + x**2)**2,
        integral_type="definite",
        lower=sp.Integer(0),
        upper=sp.oo,
        topic="Improper Integral",
        difficulty="hard",
        progressive_hints=[
            r"Let $x = \tan(\theta)$, so $1+x^2 = \sec^2(\theta)$ and $dx = \sec^2(\theta)d\theta$",
            r"The integrand becomes $\cos^2(\theta)$, with limits $0$ to $\pi/2$",
            r"Then $\int_0^{\pi/2}\cos^2(\theta)d\theta = \frac{\pi}{4}$",
        ],
    ),
    NewProblem(
        problem=r"\int_0^{\infty} e^{-x}\cos(x) dx",
        solution=r"\frac{1}{2}",
        integrand=sp.exp(-x) * sp.cos(x),
        integral_type="definite",
        lower=sp.Integer(0),
        upper=sp.oo,
        topic="Improper Integral",
        difficulty="hard",
        progressive_hints=[
            r"Let $I = \int_0^{\infty} e^{-x}\cos(x)dx$ and integrate by parts twice",
            r"You'll obtain an equation of the form $I = (\text{boundary terms}) - I$",
            r"Solve algebraically for $I$",
        ],
    ),
    NewProblem(
        problem=r"\int_0^{\pi} x \sin(x) dx",
        solution=r"\pi",
        integrand=x * sp.sin(x),
        integral_type="definite",
        lower=sp.Integer(0),
        upper=sp.pi,
        topic="Definite",
        difficulty="medium",
        progressive_hints=[
            r"Let $u = x$ and $dv = \sin(x)dx$, so $v = -\cos(x)$",
            r"Apply parts: $[-x\cos(x)]_0^{\pi} + \int_0^{\pi}\cos(x)dx$",
            r"Evaluate the boundary term and the remaining integral",
        ],
    ),
    NewProblem(
        problem=r"\int_0^{\infty} x^2 e^{-x} dx",
        solution=r"2",
        integrand=x**2 * sp.exp(-x),
        integral_type="definite",
        lower=sp.Integer(0),
        upper=sp.oo,
        topic="Improper Integral",
        difficulty="medium",
        progressive_hints=[
            r"Recall $\int_0^{\infty} x^n e^{-x}dx = n!$ (the Gamma function $\Gamma(n+1)$)",
            r"Here $n = 2$",
            r"So the value is $2! = 2$",
        ],
    ),
]
