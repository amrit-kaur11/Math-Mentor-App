import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import GraphState, get_llm


def _extract_json_object(text: str):
    """
    Extract the first valid JSON object from a model response.
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


def _clean_answer(text: str) -> str:
    if not text:
        return ""

    answer = str(text).strip()
    answer = answer.replace("$$", "").strip()
    answer = answer.replace("\\[", "").replace("\\]", "").strip()
    answer = answer.replace("\\(", "").replace("\\)", "").strip()
    answer = answer.strip("`* ")

    # Remove leading final-answer labels.
    answer = re.sub(
        r"^(final answer|answer)\s*(is|:)?\s*",
        "",
        answer,
        flags=re.IGNORECASE,
    ).strip()

    return answer


def _extract_final_answer_from_markdown(text: str) -> str:
    """
    Fallback extractor when the model does not return valid JSON.
    """
    if not text:
        return ""

    boxed = re.search(r"\\boxed\{([^{}]+)\}", text)
    if boxed:
        return _clean_answer(boxed.group(1))

    section = re.search(
        r"##\s*Final Answer\s*(.*?)(?:\n##|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if section:
        candidate = section.group(1).strip()
        candidate = candidate.splitlines()[0].strip() if candidate else ""
        if candidate:
            return _clean_answer(candidate)

    patterns = [
        r"final answer\s*(?:is|:)\s*(.+)",
        r"answer\s*(?:is|:)\s*(.+)",
        r"therefore,?\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_answer(match.group(1).splitlines()[0])

    return ""


def solver_node(state: GraphState):
    llm = get_llm()

    prompt = f"""
You are a Solver Agent.

Solve the math problem carefully.

Problem:
{state.get('parsed_problem', '')}

Topic:
{state.get('topic', '')}

Retrieved Context:
{state.get('retrieved_context', '')}

Rules:
1. Check all original constraints.
2. If a system is inconsistent, say there is no solution.
3. Keep the algebra concise.
4. Put algebra steps on separate lines.
5. Return JSON only. Do not use markdown fences.
6. The final_answer must be only the final mathematical result, not the full solution.
7. Include the solved variable in final_answer when applicable.
   Example: use "x = 5/2", not just "5/2".

Return exactly this JSON schema:
{{
  "solution_plan": "Concise student-facing solution with step-by-step reasoning. Markdown is allowed inside this string.",
  "final_answer": "Only the final answer, for example x = 5/2"
}}
"""

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are an expert math solver. Return valid JSON only. "
                    "Do not place the JSON inside markdown fences."
                )
            ),
            HumanMessage(content=prompt),
        ]
    )

    raw_text = response.content.strip()
    parsed = _extract_json_object(raw_text)

    if parsed:
        solution_plan = str(parsed.get("solution_plan") or "").strip()
        final_answer = _clean_answer(parsed.get("final_answer") or "")
    else:
        solution_plan = raw_text
        final_answer = _extract_final_answer_from_markdown(raw_text)

    # Last-resort fallback: keep the raw model text as the plan, but do not put
    # the whole plan into final_answer.
    if not solution_plan:
        solution_plan = raw_text

    if not final_answer:
        final_answer = "Unable to extract a clean final answer."

    return {
        "solution_plan": solution_plan,
        "final_answer": final_answer,
    }
