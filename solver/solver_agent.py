import sympy as sp
import re


def solve_math_problem(parsed_data):

    expression = parsed_data["normalized_expression"]

    try:
        # Split equation
        left, right = expression.split("=")

        # Define variable
        x = sp.symbols("x")

        # Convert to sympy expressions
        left_expr = sp.sympify(left)
        right_expr = sp.sympify(right)

        # Solve equation
        solution = sp.solve(left_expr - right_expr, x)

        return {
            "steps": "Solved using symbolic algebra",
            "final_answer": f"x = {solution[0]}"
        }

    except Exception as e:
        return {
            "steps": "Error during solving",
            "final_answer": str(e)
        }
