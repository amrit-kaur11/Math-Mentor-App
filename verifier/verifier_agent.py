# verifier/verifier_agent.py

import sympy as sp
import re


def extract_multiple_solutions(solution_text):
    """
    Extracts multiple numeric solutions from solver output.
    Example: 'x = -2, -3'
    Returns list of floats.
    """
    matches = re.findall(r"-?\d+\.?\d*", solution_text)
    return [float(m) for m in matches]


def verify_equation(question: str, solution_text: str):
    """
    General equation verifier for linear and quadratic equations.
    """

    try:
        x = sp.symbols("x")

        if "=" not in question:
            return {
                "verified": False,
                "reason": "Not an equation"
            }

        left, right = question.split("=")

        left_expr = sp.sympify(left)
        right_expr = sp.sympify(right)

        solutions = extract_multiple_solutions(solution_text)

        if not solutions:
            return {
                "verified": False,
                "reason": "No solutions found in output"
            }

        all_correct = True

        for val in solutions:
            left_val = left_expr.subs(x, val)
            right_val = right_expr.subs(x, val)

            if sp.simplify(left_val - right_val) != 0:
                all_correct = False
                break

        if all_correct:
            return {
                "verified": True,
                "reason": "All solutions satisfy the equation"
            }
        else:
            return {
                "verified": False,
                "reason": "One or more solutions do not satisfy equation"
            }

    except Exception as e:
        return {
            "verified": False,
            "reason": f"Verification error: {str(e)}"
        }
