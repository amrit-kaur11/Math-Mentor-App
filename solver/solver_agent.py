from sympy import symbols, Eq, solve, sympify
from sympy.parsing.sympy_parser import parse_expr


def solve_math_problem(parsed_output):
    try:
        normalized_expr = parsed_output["normalized_expression"]
        variables = parsed_output.get("variables", [])

        if not variables:
            return {
                "steps": "No variable found in equation.",
                "final_answer": "Cannot solve."
            }

        var_symbol = symbols(variables[0])

        # Split LHS and RHS
        if "=" in normalized_expr:
            lhs, rhs = normalized_expr.split("=")
        else:
            return {
                "steps": "Invalid equation format.",
                "final_answer": "Error"
            }

        lhs_expr = parse_expr(lhs)
        rhs_expr = parse_expr(rhs)

        equation = Eq(lhs_expr, rhs_expr)

        solutions = solve(equation, var_symbol)

        if not solutions:
            return {
                "steps": "No solution found.",
                "final_answer": "No solution"
            }

        steps = []

        if parsed_output["problem_type"] == "equation":
            steps.append("Step 1: Rearrange equation into standard form.")
            steps.append("Step 2: Solve for variable using symbolic algebra.")

        final_answers = [f"{var_symbol} = {sol}" for sol in solutions]

        return {
            "steps": steps,
            "final_answer": final_answers if len(final_answers) > 1 else final_answers[0]
        }

    except Exception as e:
        return {
            "steps": "Error during solving.",
            "final_answer": str(e)
        }
