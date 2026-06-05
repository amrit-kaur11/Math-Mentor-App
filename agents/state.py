import os
from typing import TypedDict, Optional, Any, Literal
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


class GraphState(TypedDict, total=False):
    """
    Shared LangGraph state.

    total=False is intentional because every node only updates part of the
    state. LangGraph still uses these keys as allowed state channels, but the
    initial state can safely start with only raw_input.
    """

    # Parser fields
    raw_input: str
    parsed_problem: str
    topic: str
    variables: Any
    constraints: Any
    needs_clarification: bool

    # Retrieval and memory context
    retrieved_context: str

    # Solver fields
    solution_plan: str
    final_answer: str

    # Verifier fields
    is_verified: bool
    verifier_critique: str
    verifier_verdict: str
    retry_needed: bool
    final_answer_override: Optional[str]
    retry_count: int
    max_retries: int

    # Final explanation
    explanation: str


class ParserOutput(BaseModel):
    problem_text: str = Field(description="Cleaned up problem text")
    topic: str = Field(description="Math topic e.g., algebra, probability, calculus, linear algebra")
    variables: str = Field(description="List of variables identified or a string. Return 'None' if none.")
    constraints: str = Field(description="List of domain constraints or a string. Return 'None' if none.")
    needs_clarification: str = Field(
        description=(
            "MUST be exactly 'True' or 'False' as a string. "
            "Set to 'True' ONLY if the input is completely broken gibberish. "
            "If it is a conversational question, ALWAYS set to 'False' so it can be answered."
        )
    )


class VerifierOutput(BaseModel):
    verified: bool = Field(
        description="True if the proposed final answer is mathematically correct."
    )

    critique: str = Field(
        description="Short verification note. Maximum 3 sentences. Do not repeat sentences.",
        max_length=800,
    )

    verdict: Literal[
        "correct",
        "incorrect",
        "inconsistent_system",
        "formatting_issue",
        "uncertain",
    ] = Field(
        default="uncertain",
        description="Verifier classification of the proposed answer.",
    )

    retry_needed: bool = Field(
        default=False,
        description=(
            "True only if the solver should retry due to a fixable arithmetic, algebraic, "
            "parsing, or reasoning mistake. False for inconsistent systems."
        ),
    )

    final_answer_override: Optional[str] = Field(
        default=None,
        description=(
            "Optional corrected final answer. Use this when the verifier can safely provide "
            "the final answer, such as 'No solution. The equations are inconsistent.'"
        ),
    )


def get_llm():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file before running the app.")

    return ChatGroq(
        temperature=0,
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=api_key,
    )
