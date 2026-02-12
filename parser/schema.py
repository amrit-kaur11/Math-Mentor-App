def get_empty_parse():
    """
    Returns abase schema for parsed math questions.
    """

    return {
        "raw_question": None,
        "problem_type": None,
        "math_domain": None,
        "variables": [],
        "degree": None,
        "normalized_expression": None,
        "is_ambiguous": False,
        "ambiguity_reson": None
    }
