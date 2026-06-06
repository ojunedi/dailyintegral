"""
Add 20 challenging integral problems to the Supabase `integrals` table.

Every `solution` here was verified by migrations/verify_new_problems.py to be
(a) mathematically correct vs SymPy and (b) parseable by the app's grader.
Ids continue from the existing 46 (47-66) and dates are unique, non-colliding.
Idempotent: upserts on the `id` primary key.

Usage (needs SUPABASE_URL + SUPABASE_SERVICE_KEY in .env.local):
    uv run python -m migrations.add_challenging_problems
"""
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# id, date, problem, solution, hint, topic, integral_type, progressive_hints
PROBLEMS = [
    # ---------------- INDEFINITE ----------------
    dict(id=47, date="2025-02-19", integral_type="indefinite",
         topic="Integration by Parts",
         problem=r"\int x^2 \ln(x) dx",
         solution=r"\frac{x^3}{3}\ln(x) - \frac{x^3}{9} + C",
         hint=r"$\text{Integration by parts with } u = \ln(x)$",
         progressive_hints=[
             r"Use integration by parts: $\int u \, dv = uv - \int v \, du$",
             r"Let $u = \ln(x)$ and $dv = x^2 dx$",
             r"Then $du = \frac{1}{x}dx$ and $v = \frac{x^3}{3}$; the leftover integral is elementary",
         ]),
    dict(id=48, date="2025-02-20", integral_type="indefinite",
         topic="Integration by Parts",
         problem=r"\int x \arctan(x) dx",
         solution=r"\frac{x^2+1}{2}\arctan(x) - \frac{x}{2} + C",
         hint=r"$\text{Parts with } u = \arctan(x)$",
         progressive_hints=[
             r"Let $u = \arctan(x)$, $dv = x \, dx$",
             r"Then $du = \frac{1}{1+x^2}dx$ and $v = \frac{x^2}{2}$",
             r"The remaining $\int \frac{x^2}{2(1+x^2)}dx$ simplifies via $\frac{x^2}{1+x^2} = 1 - \frac{1}{1+x^2}$",
         ]),
    dict(id=49, date="2025-02-21", integral_type="indefinite",
         topic="Integration by Parts",
         problem=r"\int \ln^2(x) dx",
         solution=r"x\ln(x)^2 - 2x\ln(x) + 2x + C",
         hint=r"$\text{Parts twice, with } dv = dx$",
         progressive_hints=[
             r"Let $u = \ln^2(x)$ and $dv = dx$, so $v = x$",
             r"This leaves $\int 2\ln(x) dx$ — apply parts again",
             r"Recall $\int \ln(x) dx = x\ln(x) - x$",
         ]),
    dict(id=50, date="2025-02-22", integral_type="indefinite",
         topic="Integration by Parts",
         problem=r"\int \arcsin(x) dx",
         solution=r"x\arcsin(x) + \sqrt{1-x^2} + C",
         hint=r"$\text{Parts with } u = \arcsin(x),\ dv = dx$",
         progressive_hints=[
             r"Let $u = \arcsin(x)$ and $dv = dx$",
             r"Then $du = \frac{1}{\sqrt{1-x^2}}dx$ and $v = x$",
             r"The leftover $\int \frac{x}{\sqrt{1-x^2}}dx$ yields $-\sqrt{1-x^2}$ by substitution",
         ]),
    dict(id=51, date="2025-02-23", integral_type="indefinite",
         topic="Integration by Parts",
         problem=r"\int x \sec^2(x) dx",
         solution=r"x\tan(x) + \ln(\cos(x)) + C",
         hint=r"$\text{Parts with } u = x,\ dv = \sec^2(x)dx$",
         progressive_hints=[
             r"Let $u = x$ and $dv = \sec^2(x)dx$, so $v = \tan(x)$",
             r"This leaves $\int \tan(x) dx$",
             r"Recall $\int \tan(x) dx = -\ln|\cos(x)|$",
         ]),
    dict(id=52, date="2025-02-24", integral_type="indefinite",
         topic="Integration by Parts",
         problem=r"\int x^2 \cos(x) dx",
         solution=r"x^2\sin(x) + 2x\cos(x) - 2\sin(x) + C",
         hint=r"$\text{Parts twice (tabular works well)}$",
         progressive_hints=[
             r"Let $u = x^2$, $dv = \cos(x)dx$",
             r"After one application you get $\int 2x\sin(x)dx$ — apply parts again",
             r"Each step lowers the power of $x$ by one until it vanishes",
         ]),
    dict(id=53, date="2025-02-25", integral_type="indefinite",
         topic="Trigonometric",
         problem=r"\int \sec^4(x) dx",
         solution=r"\tan(x) + \frac{1}{3}\tan(x)^3 + C",
         hint=r"$\text{Split off } \sec^2(x)\text{ and use } \sec^2 = 1 + \tan^2$",
         progressive_hints=[
             r"Write $\sec^4(x) = \sec^2(x)\cdot\sec^2(x)$",
             r"Replace one factor: $\sec^2(x) = 1 + \tan^2(x)$",
             r"Substitute $u = \tan(x)$, $du = \sec^2(x)dx$, then integrate $1 + u^2$",
         ]),
    dict(id=54, date="2025-02-26", integral_type="indefinite",
         topic="Trigonometric",
         problem=r"\int \tan^3(x) dx",
         solution=r"\frac{1}{2}\tan(x)^2 + \ln(\cos(x)) + C",
         hint=r"$\text{Use } \tan^2 = \sec^2 - 1$",
         progressive_hints=[
             r"Write $\tan^3(x) = \tan(x)(\sec^2(x) - 1)$",
             r"Split into $\int \tan(x)\sec^2(x)dx - \int \tan(x)dx$",
             r"The first is $\frac{1}{2}\tan^2(x)$ by $u=\tan x$; the second is $\ln|\cos x|$",
         ]),
    dict(id=55, date="2025-02-27", integral_type="indefinite",
         topic="Trigonometric",
         problem=r"\int \sin^3(x) dx",
         solution=r"\frac{1}{3}\cos(x)^3 - \cos(x) + C",
         hint=r"$\text{Save one } \sin(x)\text{ and use } \sin^2 = 1-\cos^2$",
         progressive_hints=[
             r"Write $\sin^3(x) = \sin(x)(1 - \cos^2(x))$",
             r"Substitute $u = \cos(x)$, $du = -\sin(x)dx$",
             r"Integrate $-(1 - u^2)$ in $u$",
         ]),
    dict(id=56, date="2025-02-28", integral_type="indefinite",
         topic="Trigonometric Substitution",
         problem=r"\int \sqrt{1-x^2} dx",
         solution=r"\frac{x\sqrt{1-x^2} + \arcsin(x)}{2} + C",
         hint=r"$\text{Substitute } x = \sin(\theta)$",
         progressive_hints=[
             r"Let $x = \sin(\theta)$, so $\sqrt{1-x^2} = \cos(\theta)$ and $dx = \cos(\theta)d\theta$",
             r"The integral becomes $\int \cos^2(\theta) d\theta$",
             r"Use $\cos^2(\theta) = \frac{1+\cos(2\theta)}{2}$, then convert back to $x$",
         ]),
    dict(id=57, date="2025-03-01", integral_type="indefinite",
         topic="Partial Fractions",
         problem=r"\int \frac{1}{x^2-1} dx",
         solution=r"\frac{1}{2}\ln\left(\frac{x-1}{x+1}\right) + C",
         hint=r"$\text{Factor and decompose into partial fractions}$",
         progressive_hints=[
             r"Factor: $\frac{1}{x^2-1} = \frac{1}{(x-1)(x+1)}$",
             r"Decompose: $\frac{1}{(x-1)(x+1)} = \frac{1/2}{x-1} - \frac{1/2}{x+1}$",
             r"Integrate each term to logarithms and combine",
         ]),
    dict(id=58, date="2025-03-02", integral_type="indefinite",
         topic="Completing the Square",
         problem=r"\int \frac{1}{x^2+2x+5} dx",
         solution=r"\frac{1}{2}\arctan\left(\frac{x+1}{2}\right) + C",
         hint=r"$\text{Complete the square in the denominator}$",
         progressive_hints=[
             r"Complete the square: $x^2+2x+5 = (x+1)^2 + 4$",
             r"Use the form $\int \frac{1}{u^2 + a^2}du = \frac{1}{a}\arctan\left(\frac{u}{a}\right)$",
             r"Here $u = x+1$ and $a = 2$",
         ]),
    dict(id=59, date="2025-03-03", integral_type="indefinite",
         topic="Substitution",
         problem=r"\int x^3 e^{x^2} dx",
         solution=r"\frac{(x^2-1)e^{x^2}}{2} + C",
         hint=r"$\text{Substitute } u = x^2,\text{ then integrate by parts}$",
         progressive_hints=[
             r"Let $u = x^2$, $du = 2x \, dx$; note $x^3 dx = x^2 \cdot x \, dx = \frac{u}{2}du$",
             r"The integral becomes $\frac{1}{2}\int u e^u du$",
             r"Integrate $u e^u$ by parts: $u e^u - e^u$, then back-substitute",
         ]),
    dict(id=60, date="2025-03-04", integral_type="indefinite",
         topic="Substitution",
         problem=r"\int \frac{1}{1+e^x} dx",
         solution=r"x - \ln(e^x + 1) + C",
         hint=r"$\text{Rewrite } \frac{1}{1+e^x} = 1 - \frac{e^x}{1+e^x}$",
         progressive_hints=[
             r"Multiply through or split: $\frac{1}{1+e^x} = 1 - \frac{e^x}{1+e^x}$",
             r"The first term integrates to $x$",
             r"For the second, substitute $u = 1+e^x$, $du = e^x dx$, giving $-\ln(1+e^x)$",
         ]),

    # ---------------- DEFINITE ----------------
    dict(id=61, date="2025-03-05", integral_type="definite",
         topic="Definite Trigonometric",
         problem=r"\int_0^{\pi/2} \sin^2(x) dx",
         solution=r"\frac{\pi}{4}",
         hint=r"$\text{Use the half-angle identity}$",
         progressive_hints=[
             r"Use $\sin^2(x) = \frac{1 - \cos(2x)}{2}$",
             r"Integrate term by term over $[0, \pi/2]$",
             r"The $\cos(2x)$ term integrates to $0$ over this interval",
         ]),
    dict(id=62, date="2025-03-06", integral_type="definite",
         topic="Definite Trigonometric",
         problem=r"\int_0^{\pi/2} \cos^4(x) dx",
         solution=r"\frac{3\pi}{16}",
         hint=r"$\text{Apply the half-angle identity twice (or Wallis)}$",
         progressive_hints=[
             r"Use $\cos^2(x) = \frac{1+\cos(2x)}{2}$, then square it",
             r"Expand and apply the half-angle identity again to $\cos^2(2x)$",
             r"Alternatively use the Wallis formula for $\int_0^{\pi/2}\cos^n$",
         ]),
    dict(id=63, date="2025-03-07", integral_type="definite",
         topic="Improper Integral",
         problem=r"\int_0^{\infty} \frac{1}{(1+x^2)^2} dx",
         solution=r"\frac{\pi}{4}",
         hint=r"$\text{Substitute } x = \tan(\theta)$",
         progressive_hints=[
             r"Let $x = \tan(\theta)$, so $1+x^2 = \sec^2(\theta)$ and $dx = \sec^2(\theta)d\theta$",
             r"The integrand becomes $\cos^2(\theta)$, with limits $0$ to $\pi/2$",
             r"Then $\int_0^{\pi/2}\cos^2(\theta)d\theta = \frac{\pi}{4}$",
         ]),
    dict(id=64, date="2025-03-08", integral_type="definite",
         topic="Improper Integral",
         problem=r"\int_0^{\infty} e^{-x}\cos(x) dx",
         solution=r"\frac{1}{2}",
         hint=r"$\text{Integrate by parts twice and solve for } I$",
         progressive_hints=[
             r"Let $I = \int_0^{\infty} e^{-x}\cos(x)dx$ and integrate by parts twice",
             r"You'll obtain an equation of the form $I = (\text{boundary terms}) - I$",
             r"Solve algebraically for $I$",
         ]),
    dict(id=65, date="2025-03-09", integral_type="definite",
         topic="Definite",
         problem=r"\int_0^{\pi} x \sin(x) dx",
         solution=r"\pi",
         hint=r"$\text{Integration by parts with } u = x$",
         progressive_hints=[
             r"Let $u = x$ and $dv = \sin(x)dx$, so $v = -\cos(x)$",
             r"Apply parts: $[-x\cos(x)]_0^{\pi} + \int_0^{\pi}\cos(x)dx$",
             r"Evaluate the boundary term and the remaining integral",
         ]),
    dict(id=66, date="2025-03-10", integral_type="definite",
         topic="Improper Integral",
         problem=r"\int_0^{\infty} x^2 e^{-x} dx",
         solution=r"2",
         hint=r"$\text{This is } \Gamma(3) = 2!$",
         progressive_hints=[
             r"Recall $\int_0^{\infty} x^n e^{-x}dx = n!$ (the Gamma function $\Gamma(n+1)$)",
             r"Here $n = 2$",
             r"So the value is $2! = 2$",
         ]),
]


def main():
    load_dotenv(os.path.join(BASE_DIR, ".env.local"))
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not service_key:
        sys.exit("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set (.env.local).")

    client = create_client(url, service_key)
    client.table("integrals").upsert(PROBLEMS, on_conflict="id").execute()

    count = client.table("integrals").select("id", count="exact").execute()
    print(f"Upserted {len(PROBLEMS)} problems. Supabase now has {count.count} integrals.")


if __name__ == "__main__":
    main()
