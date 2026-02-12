import re
from parser.schema import get_empty_parse

def normalize_expression(expression: str):
    expression = expression.replace("^", "**")
    expression = re.sub(r"\s+", "", expression)
    return expression


def parse_math_question(question: str) -> dict:
    """
    Parses a verified math question into structured form.
    """

    parsed = get_empty_parse()
    parsed["raw_question"] = question

    # Normalize spacing
    q = question.replace(" ", "")

    # ---------- Detect equation ----------
    if "=" in q:
        parsed["problem_type"] = "equation"
        parsed["math_domain"] = "algebra"

        # Detect variables
        variables = sorted(set(re.findall(r"[a-zA-Z]", q)))
        parsed["variables"] = variables

        # Detect degree (basic polynomial)
        degrees = re.findall(r"\^(\d+)", q)
        if degrees:
            parsed["degree"] = max(map(int, degrees))
        else:
            parsed["degree"] = 1

        # Normalize expression
        parsed["normalized_expression"] = normalize_expression(q)

    # ---------- Detect derivative ----------
    elif "derivative" in question.lower():
        parsed["problem_type"] = "derivative"
        parsed["math_domain"] = "calculus"

    else:
        parsed["is_ambiguous"] = True
        parsed["ambiguity_reason"] = "Unable to classify problem type"

    # ---------- Ambiguity checks ----------
    if len(parsed["variables"]) > 1:
        parsed["is_ambiguous"] = True
        parsed["ambiguity_reason"] = "Multiple variables detected"

    return parsed
