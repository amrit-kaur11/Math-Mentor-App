from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import GraphState, VerifierOutput, get_llm


DEFAULT_MAX_RETRIES = 1


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def verifier_node(state: GraphState):
    llm = get_llm()
    structured_llm = llm.with_structured_output(VerifierOutput)

    current_retry_count = _safe_int(state.get("retry_count", 0), 0)
    max_retries = _safe_int(state.get("max_retries", DEFAULT_MAX_RETRIES), DEFAULT_MAX_RETRIES)

    prompt = f"""
Verify the proposed math answer.

Original problem:
{state.get("parsed_problem", "")}

Proposed answer:
{state.get("final_answer", "")}

Task-aware verification rules:
1. Return only the structured output matching the VerifierOutput schema.
2. Keep critique under 3 short sentences.
3. Do not repeat any sentence.
4. Do not generate a long explanation.
5. Do not solve the problem from scratch unless it is necessary to verify the answer.
6. Identify the task type before judging correctness.

For equation-solving problems:
- Check whether the proposed answer satisfies the original equation.
- For quadratics, verify that each proposed root satisfies the equation if practical.

For differentiation problems:
- Do not use substitution into the original expression.
- Check whether the proposed answer is the correct derivative.
- If the derivative is correct, verified = true.
- If the derivative is correct but formatting is imperfect, verified = true and retry_needed = false.

For integration problems:
- Check by differentiating the proposed antiderivative if practical.
- Do not mark the answer wrong only because the constant of integration is formatted differently.

For simplification problems:
- Check mathematical equivalence.
- Do not require a specific style if the expression is equivalent.

For systems of equations:
- If a candidate solution satisfies all original equations, verdict = "correct".
- If the equations contradict each other and the correct answer is no solution, verdict = "inconsistent_system".
- If the proposed answer correctly concludes no solution, verified = true.
- If the proposed answer fails to conclude no solution, verified = false.
- retry_needed should be false for inconsistent systems.
- If the correct conclusion is no solution, set final_answer_override to:
"No solution. The equations are inconsistent."

Retry rules:
1. retry_needed should be true only when the final answer is definitely wrong and the solver can likely fix it.
2. retry_needed should be false for formatting issues, missing explanation, missing verification, or minor wording issues.
3. retry_needed should be false when the answer is mathematically acceptable.
4. retry_needed should be false when the problem is ambiguous and cannot be fixed without user clarification.
5. Current retry count: {current_retry_count}
6. Maximum retries allowed: {max_retries}

Good critique example:
"The proposed derivative is correct. The answer matches the power rule applied to each term."

Return these exact fields:
- verified
- critique
- verdict
- retry_needed
- final_answer_override
"""

    try:
        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You are a strict but fair math verifier. "
                        "Return concise structured output only. "
                        "Never repeat sentences. "
                        "Never produce more than 3 sentences in critique. "
                        "Do not request a retry for formatting-only issues."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )

        if isinstance(result, dict):
            if "is verified" in result:
                result["verified"] = result.pop("is verified")
            if "is_verified" in result:
                result["verified"] = result.pop("is_verified")

            result = VerifierOutput(**result)

    except Exception as e:
        print(f"Verifier structured output failed: {e}")

        result = VerifierOutput(
            verified=False,
            critique=(
                "Verifier failed to produce valid structured output. "
                "Proceeding safely without retrying the solver."
            ),
            verdict="uncertain",
            retry_needed=False,
            final_answer_override=None,
        )

    raw_retry_needed = bool(result.retry_needed)
    verdict = result.verdict or "uncertain"
    final_answer_override = result.final_answer_override or None

    # Hard safety rules to prevent infinite solver-verifier loops.
    if result.verified:
        effective_retry_needed = False
    elif final_answer_override:
        effective_retry_needed = False
    elif verdict == "inconsistent_system":
        effective_retry_needed = False
    elif raw_retry_needed and current_retry_count < max_retries:
        effective_retry_needed = True
    else:
        effective_retry_needed = False

    new_retry_count = current_retry_count + 1 if effective_retry_needed else current_retry_count

    critique = result.critique or ""

    if raw_retry_needed and not effective_retry_needed and not result.verified:
        if current_retry_count >= max_retries:
            critique = (
                f"{critique} Maximum retry limit reached, so the workflow will proceed to explanation."
            ).strip()

    print(f"Verifier critique: {critique}")
    print(f"Verifier verdict: {verdict}")
    print(f"Raw retry needed: {raw_retry_needed}")
    print(f"Effective retry needed: {effective_retry_needed}")
    print(f"Retry count: {new_retry_count}/{max_retries}")
    print(f"Final answer override: {final_answer_override}")

    return {
        "is_verified": result.verified,
        "verifier_critique": critique,
        "verifier_verdict": verdict,
        "retry_needed": effective_retry_needed,
        "final_answer_override": final_answer_override,
        "retry_count": new_retry_count,
        "max_retries": max_retries,
    }