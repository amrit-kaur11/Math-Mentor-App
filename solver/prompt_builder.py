# solver/prompt_builder.py

def build_solver_prompt(question, parsed_output, retrieved_docs):
    """
    Builds a grounded prompt for the solver LLM.
    """

    knowledge_block = "\n".join(
        [f"- {doc}" for doc in retrieved_docs]
    )

    prompt = f"""
You are a math tutor.

Use ONLY the knowledge provided below to solve the problem.
Explain step-by-step clearly.

--- KNOWLEDGE ---
{knowledge_block}

--- PARSED STRUCTURE ---
Problem Type: {parsed_output.get('problem_type')}
Math Domain: {parsed_output.get('math_domain')}
Variables: {parsed_output.get('variables')}
Degree: {parsed_output.get('degree')}

--- QUESTION ---
{question}

--- SOLUTION ---
"""

    return prompt
