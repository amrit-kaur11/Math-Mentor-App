import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import GraphState, get_llm


# -------------------------------------------------
# Helper functions
# -------------------------------------------------

def _json_dumps(payload: dict) -> str:
    """
    Store structured solution data as a JSON string.
    app.py will parse this and render it cleanly.
    """
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _extract_json_object(text: str):
    """
    Extracts the first valid JSON object from an LLM response.
    Handles cases where the model accidentally wraps JSON in markdown.
    """
    if not text:
        return None

    cleaned = text.strip()

    cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^```", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return None


def _extract_latex_command_argument(text: str, command: str = "boxed") -> str:
    """
    Extracts balanced LaTeX command content.
    Example:
        \\boxed{1 + \\frac{z}{y}} -> 1 + \\frac{z}{y}
    """
    if not text:
        return ""

    token = f"\\{command}" + "{"
    start = text.find(token)

    if start == -1:
        return ""

    index = start + len(token)
    depth = 1
    result = []

    while index < len(text):
        char = text[index]

        if char == "{":
            depth += 1
            result.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(result).strip()
            result.append(char)
        else:
            result.append(char)

        index += 1

    return ""


def _clean_final_answer(answer: str) -> str:
    """
    Cleans final answer text so the UI receives only the actual answer.
    """
    if not answer:
        return ""

    text = str(answer).strip()

    boxed = _extract_latex_command_argument(text, "boxed")
    if boxed:
        text = boxed

    text = text.replace("$$", "").strip()
    text = text.replace("\\[", "").replace("\\]", "").strip()
    text = text.replace("\\(", "").replace("\\)", "").strip()
    text = text.strip("`* ")

    return text

def _is_variable_dependent_denominator(denominator: str) -> bool:
    """
    Returns True only if the denominator contains an actual variable.
    Ignores constants like 1, -1, 2, 2(1), etc.
    """
    if not denominator:
        return False

    cleaned = str(denominator).strip()

    # Remove common LaTeX commands before checking for variables.
    cleaned = re.sub(r"\\[a-zA-Z]+", "", cleaned)

    # Remove numbers, spaces, braces, parentheses, and arithmetic symbols.
    variable_part = re.sub(r"[0-9\s{}().,+\-*/^=]", "", cleaned)

    return bool(variable_part)

def _infer_conditions_from_text(*texts) -> list:
    """
    Infers simple denominator restrictions.
    Example:
        x = 1 + \\frac{z}{y} -> y ≠ 0
        x = 1 + z/y -> y ≠ 0
    """
    joined = " ".join(str(t) for t in texts if t)
    if not joined:
        return []

    conditions = []

    # LaTeX fractions: \frac{z}{y}
    latex_denominators = re.findall(r"\\frac\{[^{}]+\}\{([^{}]+)\}", joined)
    for denominator in latex_denominators:
        denominator = denominator.strip()
        if _is_variable_dependent_denominator(denominator):
            conditions.append(f"{denominator} ≠ 0")

    # Plain slash fractions: z/y
    plain_denominators = re.findall(r"/\s*([a-zA-Z][a-zA-Z0-9_]*)", joined)
    for denominator in plain_denominators:
        denominator = denominator.strip()
        if _is_variable_dependent_denominator(denominator):
            conditions.append(f"{denominator} ≠ 0")

    unique = []
    for condition in conditions:
        normalized = condition.replace("\\neq", "≠").replace("\\ne", "≠").replace("!=", "≠")
        if normalized not in unique:
            unique.append(normalized)

    return unique


def _normalize_payload(payload: dict, parsed_problem: str, final_answer: str) -> dict:
    """
    Ensures the explainer always returns the exact schema expected by app.py.
    """
    if not isinstance(payload, dict):
        payload = {}

    cleaned_final_answer = _clean_final_answer(
        payload.get("final_answer") or final_answer or ""
    )

    problem = payload.get("problem") or parsed_problem or ""

    conditions = payload.get("conditions") or []
    if isinstance(conditions, str):
        conditions = [conditions]
    if not isinstance(conditions, list):
        conditions = []

    inferred_conditions = _infer_conditions_from_text(
        cleaned_final_answer,
        json.dumps(payload, ensure_ascii=False),
    )

    all_conditions = []
    for condition in conditions + inferred_conditions:
        condition = str(condition).strip()
        if condition and condition not in all_conditions:
            all_conditions.append(condition)

    steps = payload.get("steps") or []
    if not isinstance(steps, list):
        steps = []

    normalized_steps = []
    for index, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            normalized_steps.append(
                {
                    "title": str(step.get("title") or f"Step {index}").strip(),
                    "text": str(step.get("text") or "").strip(),
                    "math": step.get("math") or "",
                }
            )
        else:
            normalized_steps.append(
                {
                    "title": f"Step {index}",
                    "text": str(step).strip(),
                    "math": "",
                }
            )

    verification = payload.get("verification") or []
    if isinstance(verification, str):
        verification = [verification]
    if not isinstance(verification, list):
        verification = []

    explanation = str(payload.get("explanation") or "").strip()

    return {
        "problem": str(problem).strip(),
        "final_answer": cleaned_final_answer,
        "conditions": all_conditions,
        "steps": normalized_steps,
        "verification": [str(v).strip() for v in verification if str(v).strip()],
        "explanation": explanation,
    }


def _fallback_payload(parsed_problem: str, solution_plan: str, final_answer: str, verifier_critique: str = "") -> dict:
    """
    Used only if the LLM fails to return valid JSON.
    """
    cleaned_final_answer = _clean_final_answer(final_answer)

    conditions = _infer_conditions_from_text(cleaned_final_answer, solution_plan)

    steps = []

    if solution_plan:
        steps.append(
            {
                "title": "Use the solver's method",
                "text": "The solver produced the following solution plan.",
                "math": "",
            }
        )
        steps.append(
            {
                "title": "Solution details",
                "text": str(solution_plan).strip(),
                "math": "",
            }
        )

    if cleaned_final_answer:
        steps.append(
            {
                "title": "Final expression",
                "text": "The variable is isolated to obtain the final answer.",
                "math": cleaned_final_answer,
            }
        )

    return {
        "problem": parsed_problem or "",
        "final_answer": cleaned_final_answer,
        "conditions": conditions,
        "steps": steps,
        "verification": [],
        "explanation": verifier_critique or "",
    }


# -------------------------------------------------
# Main Explainer Node
# -------------------------------------------------

def explainer_node(state: GraphState):
    llm = get_llm()

    parsed_problem = state.get("parsed_problem", "")
    solution_plan = state.get("solution_plan", "")
    final_answer = state.get("final_answer", "")
    is_verified = state.get("is_verified", False)
    verifier_critique = state.get("verifier_critique", "N/A")
    verifier_verdict = state.get("verifier_verdict", "uncertain")
    retry_needed = state.get("retry_needed", False)
    final_answer_override = state.get("final_answer_override")

    # -------------------------------------------------
    # Case 1: verifier already produced a corrected answer
    # -------------------------------------------------
    if final_answer_override:
        cleaned_override = _clean_final_answer(final_answer_override)

        payload = {
            "problem": parsed_problem,
            "final_answer": cleaned_override,
            "conditions": _infer_conditions_from_text(cleaned_override, verifier_critique),
            "steps": [
                {
                    "title": "Use the verifier's corrected result",
                    "text": "The verifier identified the corrected final answer. The original solver result should not be used.",
                    "math": "",
                }
            ],
            "verification": [],
            "explanation": verifier_critique,
        }

        payload = _normalize_payload(payload, parsed_problem, cleaned_override)

        return {
            "explanation": _json_dumps(payload),
            "final_answer": payload["final_answer"],
        }

    # -------------------------------------------------
    # Case 2: inconsistent system
    # -------------------------------------------------
    if verifier_verdict == "inconsistent_system":
        payload = {
            "problem": parsed_problem,
            "final_answer": "No solution. The equations are inconsistent.",
            "conditions": [],
            "steps": [
                {
                    "title": "Check consistency",
                    "text": "The equations contradict each other, so no value satisfies the full system.",
                    "math": "",
                }
            ],
            "verification": [],
            "explanation": verifier_critique,
        }

        payload = _normalize_payload(payload, parsed_problem, payload["final_answer"])

        return {
            "explanation": _json_dumps(payload),
            "final_answer": payload["final_answer"],
        }

    # -------------------------------------------------
    # Normal case: generate clean structured JSON
    # -------------------------------------------------
    prompt = f"""
You are a Math Tutor Agent.

Your job is to convert the solver's result into a clean, student-facing structured solution.

Critical rules:
1. Return valid JSON only.
2. Do not use Markdown headings.
3. Do not wrap the JSON in ```json or any code block.
4. Do not expose internal agent architecture.
5. Do not say phrases like:
   - "solver's solution plan was not provided"
   - "solver's solution plan is not provided"
   - "the internal agent"
   - "the system prompt"
6. Do not create a different final answer.
7. The final_answer field must include the solved variable.
   Example: use "x = 1 + \\frac{{z}}{{y}}", not just "1 + \\frac{{z}}{{y}}".
8. If the question asks "what does x equal?", the final answer must start with "x =".
9. If division by a variable or expression occurs, add the required condition.
   Example: dividing by y means conditions must include "y ≠ 0".
10. Include student-facing verification only when it is useful.
    - For equation-solving problems, verify by substitution.
    - For quadratic equations, verify by substituting each root if concise.
    - For integration problems, verify by differentiating the result if concise.
    - For simple arithmetic, simplification, or very short derivative problems, use an empty verification list.
11. Keep explanations concise and student-friendly.
12. Equations must be LaTeX strings.
13. Each algebra step must be separate.
14. Prefer the simplest valid algebra path.
15. Avoid unnecessary transformations such as moving everything to one side unless required.
16. Use at most 5 steps for simple algebra problems.
17. In the problem field, write a clean mathematical version of the task.
   Example: "Solve for x: y(x - 1) = z"

Student's math problem:
{parsed_problem}

Solver's solution plan:
{solution_plan}

Solver's final answer:
{final_answer}

Verification status:
{"Verified as correct." if is_verified else "Verifier found an issue."}

Verifier verdict:
{verifier_verdict}

Retry needed:
{retry_needed}

Verifier notes:
{verifier_critique}

Return this exact JSON schema:

{{
  "problem": "LaTeX or clean text version of the original problem",
  "final_answer": "Final answer with the solved variable included, for example x = 1 + \\frac{{z}}{{y}}",
  "conditions": ["Any required condition such as y ≠ 0"],
  "steps": [
    {{
      "title": "Short step title",
      "text": "Brief explanation of this step",
      "math": "One LaTeX equation or aligned expression for this step"
    }}
  ],
  "verification": [
  "Optional verification line in LaTeX. Leave this list empty if verification is unnecessary or repetitive."
],
  "explanation": "Optional short summary. Leave empty if steps are enough."
}}

For the example y(x - 1) = z solved for x, the verification should look like:
[
  "y\\\\left(\\\\left(1 + \\\\frac{{z}}{{y}}\\\\right) - 1\\\\right)",
  "= y\\\\left(\\\\frac{{z}}{{y}}\\\\right)",
  "= z"
]
"""

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a precise math tutor. "
                    "You return valid JSON only. "
                    "You produce clean student-facing math explanations. "
                    "You never expose internal solver or agent details."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    parsed_payload = _extract_json_object(response.content)

    if parsed_payload is None:
        payload = _fallback_payload(
            parsed_problem=parsed_problem,
            solution_plan=solution_plan,
            final_answer=final_answer,
            verifier_critique=verifier_critique,
        )
    else:
        payload = _normalize_payload(
            payload=parsed_payload,
            parsed_problem=parsed_problem,
            final_answer=final_answer,
        )

    return {
        "explanation": _json_dumps(payload),
        "final_answer": payload["final_answer"],
    }