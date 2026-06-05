import streamlit as st
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

from agents.parser import parse_image, parse_audio
from agents.graph import build_graph
from agents.memory import save_interaction, get_recent_history


# -----------------------------
# Session State
# -----------------------------

def init_session():
    if "raw_input" not in st.session_state:
        st.session_state.raw_input = ""

    if "input_processed" not in st.session_state:
        st.session_state.input_processed = False

    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = None

    if "workflow_error" not in st.session_state:
        st.session_state.workflow_error = ""

    if "agent_traces" not in st.session_state:
        st.session_state.agent_traces = []

    if "show_error_report" not in st.session_state:
        st.session_state.show_error_report = False

    if "feedback_message" not in st.session_state:
        st.session_state.feedback_message = ""

    if "chat_history_items" not in st.session_state:
        st.session_state.chat_history_items = []

    if "active_chat_id" not in st.session_state:
        st.session_state.active_chat_id = None

    if "last_saved_chat_key" not in st.session_state:
        st.session_state.last_saved_chat_key = ""



# -----------------------------
# Agent Runner
# -----------------------------

def run_agents(user_input: str):
    graph = build_graph()
    initial_state = {"raw_input": user_input}

    st.session_state.agent_traces.clear()
    st.session_state.feedback_message = ""
    st.session_state.show_error_report = False
    st.session_state.workflow_error = ""
    st.session_state.workflow_state = None

    with st.spinner("Agents are analyzing the problem..."):
        try:
            for output in graph.stream(initial_state):
                for key, value in output.items():
                    st.session_state.agent_traces.append((key, value))
                    st.session_state.workflow_state = value

                    if hasattr(value, "get") and value.get("needs_clarification"):
                        st.warning("Parser Agent detected ambiguity in the question. Please clarify.")
                        return False

            return True

        except Exception as e:
            st.session_state.workflow_error = str(e)
            st.session_state.workflow_state = None
            st.session_state.agent_traces.append(
                (
                    "workflow_error",
                    {"error": str(e)},
                )
            )
            return False



# -----------------------------
# CSS
# -----------------------------

def inject_custom_css():
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #05000f;
            --purple-main: #a855f7;
            --purple-light: #d8b4fe;
            --purple-hot: #ec5cff;
            --cyan-glow: #38bdf8;
            --text-main: #f8f5ff;
            --text-muted: rgba(248, 245, 255, 0.72);
            --border-soft: rgba(216, 180, 254, 0.22);
        }

        html, body, [data-testid="stAppViewContainer"], .stApp {
            min-height: 100%;
            color: var(--text-main);
            background:
                radial-gradient(circle at 12% 12%, rgba(168, 85, 247, 0.34) 0, rgba(168, 85, 247, 0.15) 18rem, transparent 34rem),
                radial-gradient(circle at 88% 15%, rgba(236, 72, 153, 0.22) 0, rgba(236, 72, 153, 0.08) 16rem, transparent 34rem),
                radial-gradient(circle at 50% 90%, rgba(56, 189, 248, 0.14) 0, rgba(56, 189, 248, 0.05) 16rem, transparent 34rem),
                linear-gradient(135deg, #05000f 0%, #090018 42%, #120024 100%) !important;
            background-attachment: fixed;
        }

        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            background:
                linear-gradient(rgba(255, 255, 255, 0.022) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.022) 1px, transparent 1px);
            background-size: 48px 48px;
            mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.42), transparent 78%);
        }

        [data-testid="stAppViewContainer"]::after {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 0;
            background:
                radial-gradient(circle at 50% 0%, rgba(216, 180, 254, 0.14), transparent 44%),
                radial-gradient(circle at 0% 70%, rgba(168, 85, 247, 0.16), transparent 38%);
            filter: blur(2px);
        }

        .main .block-container {
            position: relative;
            z-index: 1;
            max-width: 1320px !important;
            width: min(92vw, 1320px) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 3.2rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-bottom: 4rem !important;
        }

        [data-testid="stHeader"] {
            background: rgba(5, 0, 15, 0.58) !important;
            backdrop-filter: blur(18px);
        }

        section[data-testid="stSidebar"] {
            width: 310px !important;
            min-width: 310px !important;
            background:
                radial-gradient(circle at 40% 0%, rgba(168, 85, 247, 0.28), transparent 34%),
                linear-gradient(180deg, rgba(12, 4, 27, 0.94), rgba(6, 0, 15, 0.96)) !important;
            border-right: 1px solid rgba(216, 180, 254, 0.20);
            box-shadow: 18px 0 54px rgba(168, 85, 247, 0.12);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text-main);
        }

        .sidebar-header {
            padding: 1.2rem 0.4rem 1rem 0.4rem;
            margin-bottom: 0.8rem;
        }

        .sidebar-title {
            font-size: 1.35rem;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: -0.03em;
            text-shadow: 0 0 16px rgba(168, 85, 247, 0.55);
        }

        .sidebar-subtitle {
            margin-top: 0.25rem;
            font-size: 0.78rem;
            font-weight: 800;
            color: rgba(248, 245, 255, 0.52);
            text-transform: uppercase;
            letter-spacing: 0.10em;
        }

        .no-history-text {
            margin: 0.6rem 0.4rem;
            color: rgba(248, 245, 255, 0.58);
            font-size: 0.9rem;
            font-weight: 600;
        }

        .history-footer {
            margin-top: 1rem;
            padding: 0.5rem 0.4rem;
            color: rgba(248, 245, 255, 0.46);
            font-size: 0.78rem;
            line-height: 1.4;
        }

        section[data-testid="stSidebar"] .stButton > button {
            background: transparent !important;
            color: rgba(248, 245, 255, 0.78) !important;
            border: 1px solid transparent !important;
            border-radius: 12px !important;
            box-shadow: none !important;
            padding: 0.72rem 0.85rem !important;
            margin: 0.1rem 0 !important;
            font-size: 0.92rem !important;
            font-weight: 650 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            transition: background 160ms ease, border 160ms ease, color 160ms ease;
        }

        section[data-testid="stSidebar"] .stButton > button:hover,
        section[data-testid="stSidebar"] .stButton > button:focus {
            background: rgba(168, 85, 247, 0.16) !important;
            border: 1px solid rgba(216, 180, 254, 0.20) !important;
            color: #ffffff !important;
            transform: none !important;
            box-shadow: none !important;
        }

        .app-hero {
            margin-bottom: 2rem;
            max-width: 1180px;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 13px;
            border-radius: 999px;
            background: rgba(168, 85, 247, 0.14);
            border: 1px solid rgba(216, 180, 254, 0.28);
            color: #e9d5ff;
            font-size: 0.86rem;
            font-weight: 800;
            margin-bottom: 1rem;
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.14);
        }

        .hero-title {
            font-size: clamp(2.7rem, 5vw, 4.3rem);
            line-height: 1.02;
            font-weight: 900;
            letter-spacing: -0.055em;
            color: #ffffff;
            text-shadow:
                0 0 18px rgba(168, 85, 247, 0.62),
                0 0 34px rgba(236, 92, 255, 0.26);
            margin-bottom: 0.85rem;
        }

        .hero-subtitle {
            max-width: 860px;
            font-size: 1.05rem;
            line-height: 1.65;
            color: rgba(248, 245, 255, 0.78);
            margin-bottom: 1.8rem;
        }

        .input-label {
            font-size: 0.92rem;
            font-weight: 800;
            color: rgba(248, 245, 255, 0.88);
            margin-bottom: 0.5rem;
        }

        div[data-testid="stRadio"] {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
            margin-bottom: 1.4rem !important;
        }

        div[data-testid="stRadio"] label {
            font-weight: 700 !important;
            color: var(--text-main) !important;
        }

        textarea,
        input,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div {
            background: rgba(9, 2, 24, 0.82) !important;
            color: var(--text-main) !important;
            border-color: rgba(216, 180, 254, 0.30) !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }

        textarea {
            min-height: 145px !important;
            font-size: 1rem !important;
        }

        textarea:focus,
        input:focus,
        div[data-baseweb="input"]:focus-within > div,
        div[data-baseweb="textarea"]:focus-within > div {
            border-color: rgba(236, 92, 255, 0.66) !important;
            box-shadow:
                0 0 0 1px rgba(236, 92, 255, 0.26),
                0 0 24px rgba(168, 85, 247, 0.20) !important;
        }

        .stButton > button,
        .stDownloadButton > button {
            background:
                linear-gradient(135deg, rgba(168, 85, 247, 0.96), rgba(236, 92, 255, 0.88)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            border-radius: 14px !important;
            font-weight: 800 !important;
            padding: 0.72rem 1.35rem !important;
            margin-top: 0.4rem !important;
            box-shadow:
                0 12px 28px rgba(168, 85, 247, 0.26),
                0 0 28px rgba(236, 92, 255, 0.22);
            transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.08);
            box-shadow:
                0 16px 34px rgba(168, 85, 247, 0.32),
                0 0 38px rgba(236, 92, 255, 0.30);
        }

        [data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.035);
            border: 1px dashed rgba(216, 180, 254, 0.32);
            border-radius: 18px;
            padding: 16px;
            box-shadow: none;
        }

        .output-start {
            margin-top: 3.2rem;
        }

        .output-eyebrow {
            margin-top: 2.4rem;
            margin-bottom: 0.4rem;
            color: #d8b4fe;
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            text-shadow: 0 0 14px rgba(168, 85, 247, 0.42);
        }

        .clean-section-title {
            margin-top: 0.7rem;
            margin-bottom: 0.9rem;
            color: #ffffff;
            font-size: 1.45rem;
            font-weight: 900;
            letter-spacing: -0.03em;
            text-shadow: 0 0 16px rgba(168, 85, 247, 0.26);
        }

        .clean-subtitle {
            margin-top: 1.2rem;
            margin-bottom: 0.5rem;
            color: rgba(248, 245, 255, 0.86);
            font-size: 1rem;
            font-weight: 800;
        }

        .clean-divider {
            margin-top: 2.2rem;
            margin-bottom: 1.5rem;
            height: 1px;
            width: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(216, 180, 254, 0.26),
                rgba(236, 92, 255, 0.18),
                transparent
            );
        }

        .condition-pill {
            display: inline-block;
            background: rgba(168, 85, 247, 0.16);
            border: 1px solid rgba(216, 180, 254, 0.44);
            color: #f3e8ff;
            padding: 7px 12px;
            border-radius: 999px;
            font-weight: 700;
            margin: 4px 8px 4px 0;
            box-shadow: 0 0 18px rgba(168, 85, 247, 0.16);
        }

        .step-title {
            font-size: 1.12rem;
            font-weight: 900;
            color: #ffffff;
            margin-top: 1.2rem;
            margin-bottom: 0.35rem;
            text-shadow: 0 0 12px rgba(168, 85, 247, 0.24);
        }

        .muted-text {
            color: rgba(248, 245, 255, 0.68);
            font-size: 0.96rem;
        }

        .success-text {
            color: #bbf7d0;
            font-weight: 700;
            margin-top: 0.8rem;
        }

        .warning-text {
            color: #fecaca;
            font-weight: 700;
            margin-top: 0.8rem;
        }

        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stVerticalBlockBorderWrapper"]:has(h1),
        [data-testid="stVerticalBlockBorderWrapper"]:has(h2),
        [data-testid="stVerticalBlockBorderWrapper"]:has(h3),
        [data-testid="stVerticalBlockBorderWrapper"]:has(h4) {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
        }

        [data-testid="stAlert"] {
            border-radius: 12px !important;
            background: rgba(20, 8, 38, 0.72) !important;
            border: 1px solid rgba(216, 180, 254, 0.16) !important;
            box-shadow: none !important;
        }

        div[data-testid="stExpander"] {
            background: rgba(8, 2, 20, 0.62);
            border: 1px solid rgba(216, 180, 254, 0.18);
            border-radius: 14px;
            box-shadow: none;
        }

        hr {
            border-color: rgba(216, 180, 254, 0.18);
        }

        code {
            background: rgba(168, 85, 247, 0.14) !important;
            color: #f3e8ff !important;
            border-radius: 8px;
        }

        .katex-display {
            margin: 0.8rem 0 1.2rem 0 !important;
        }

        @media (max-width: 900px) {
            .main .block-container {
                width: 94vw !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .hero-title {
                font-size: 2.5rem;
            }

            section[data-testid="stSidebar"] {
                width: 290px !important;
                min-width: 290px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



# -----------------------------
# Text / JSON Cleanup Helpers
# -----------------------------

def sanitize_user_facing_text(text: str) -> str:
    """
    Removes internal or weak agent phrases from user-facing output.
    """
    if not text:
        return ""

    cleaned = str(text)

    replacements = [
        (
            r"The solver[’']s solution plan is not provided,?\s*but the steps they took to solve "
            r"(?:the equation|the problem) are as follows:?",
            "We solve it as follows:",
        ),
        (
            r"The solver[’']s solution plan is not provided\.?",
            "",
        ),
        (
            r"the steps they took to solve (?:the equation|the problem) are as follows:?",
            "we solve it as follows:",
        ),
        (
            r"Solver'?s solution plan is not provided\.?",
            "",
        ),
    ]

    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def strip_duplicate_solution_headings(text: str) -> str:
    """
    Removes headings that are now handled by the new UI structure.
    """
    if not text:
        return ""

    cleaned = text

    heading_patterns = [
        r"^#+\s*Final Answer\s*&\s*Explanation\s*$",
        r"^#+\s*Problem Check\s*$",
        r"^#+\s*Explanation\s*$",
        r"^#+\s*Verification\s*$",
        r"^#+\s*Final Answer\s*$",
    ]

    for pattern in heading_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def clean_latex_text(value: str) -> str:
    """
    Cleans common LaTeX wrappers before passing text to st.latex().
    """
    if value is None:
        return ""

    text = str(value).strip()

    text = text.replace("$$", "").strip()

    if text.startswith("\\[") and text.endswith("\\]"):
        text = text[2:-2].strip()

    if text.startswith("$") and text.endswith("$"):
        text = text[1:-1].strip()

    return text

def is_natural_language_prompt(text: str) -> bool:
    """
    Detects whether the input is a normal question/sentence rather than pure math.
    Prevents Streamlit from rendering full English prompts as LaTeX.
    """
    if not text:
        return False

    lowered = str(text).lower()

    question_words = [
        "what",
        "find",
        "solve",
        "calculate",
        "differentiate",
        "integrate",
        "does",
        "equal",
        "if ",
        "given",
    ]

    return "?" in lowered or any(word in lowered for word in question_words)


def extract_latex_command_argument(text: str, command: str = "boxed") -> str:
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


def clean_final_answer_candidate(candidate: str, problem: str = "") -> str:
    """
    Extracts only the actual final answer from noisy markdown/agent output.
    Prevents full explanations from being rendered as LaTeX.
    """
    if not candidate:
        return ""

    text = str(candidate).strip()

    boxed = extract_latex_command_argument(text, "boxed")
    if boxed:
        answer = boxed
    else:
        answer = ""

        patterns = [
            r"final answer\s*(?:is|:)\s*:?\s*(.+)",
            r"the final answer\s*(?:is|:)\s*:?\s*(.+)",
            r"answer\s*(?:is|:)\s*:?\s*(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                break

        if not answer:
            # If it is already short and math-like, use it directly.
            if len(text) < 100 and looks_like_math(text) and "###" not in text:
                answer = text

    if not answer:
        return ""

    # Stop at the next markdown heading or sentence block.
    answer = re.split(r"\n|###|##|Verification|Step-by-Step|Problem Check", answer)[0].strip()

    answer = answer.replace("$", "").strip()
    answer = answer.replace("\\(", "").replace("\\)", "").strip()
    answer = answer.replace("\\[", "").replace("\\]", "").strip()
    answer = answer.strip("`* ")

    # If solving for x and the extracted answer is only an expression, prefix x =
    lowered_problem = str(problem).lower()
    if (
        "x" in lowered_problem
        and "=" not in answer
        and answer
        and not answer.lower().startswith("x")
    ):
        answer = f"x = {answer}"

    return answer.strip()


def looks_like_math(text: str) -> bool:
    if not text:
        return False

    candidate = clean_latex_text(text)

    if is_natural_language_prompt(candidate):
        return False

    math_signals = [
        "=",
        "\\frac",
        "^",
        "_",
        "+",
        "/",
        "\\left",
        "\\right",
        "\\sqrt",
        "\\int",
        "\\sum",
        "\\cdot",
        "\\times",
        "≠",
    ]

    has_math_signal = any(signal in candidate for signal in math_signals)

    # Avoid treating long English explanations as math.
    words = re.findall(r"\b[a-zA-Z]{3,}\b", candidate)
    if len(words) > 4:
        return False

    return has_math_signal


def render_math_or_text(value: str, force_math: bool = False):
    """
    Renders equations using st.latex and normal explanations using markdown.
    """
    if not value:
        return

    cleaned = clean_latex_text(value)
    cleaned = sanitize_user_facing_text(cleaned)

    if not cleaned:
        return

    if force_math and not is_natural_language_prompt(cleaned):
        st.latex(cleaned)
    elif looks_like_math(cleaned):
        st.latex(cleaned)
    else:
        st.markdown(cleaned)


def safe_parse_solution(raw_output):
    """
    Attempts to parse a structured JSON solution from the agent output.
    Falls back safely if the output is plain markdown/text.
    """
    if isinstance(raw_output, dict):
        return raw_output

    if not isinstance(raw_output, str):
        return None

    text = raw_output.strip()

    # Remove markdown JSON fences if present.
    text = re.sub(r"^```json", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Try extracting the first JSON object inside a longer response.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return None


def coerce_to_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [item for item in value if str(item).strip()]

    if isinstance(value, tuple):
        return [item for item in value if str(item).strip()]

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return []

        # Split only when it clearly looks like a multi-line list.
        if "\n" in cleaned:
            return [line.strip("-• ").strip() for line in cleaned.splitlines() if line.strip()]

        return [cleaned]

    return [str(value)]


def normalize_condition(condition: str) -> str:
    condition = str(condition).strip()
    condition = condition.replace("\\neq", "≠")
    condition = condition.replace("\\ne", "≠")
    condition = condition.replace("!=", "≠")
    condition = condition.replace("not equal to", "≠")
    return condition

def is_variable_dependent_denominator(denominator: str) -> bool:
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

def is_meaningful_condition(condition: str) -> bool:
    """
    Keeps only real domain restrictions.
    Removes useless constant restrictions like 4 ≠ 0.
    """
    if not condition:
        return False

    normalized = normalize_condition(condition)
    normalized = normalized.replace(" ", "")

    match = re.fullmatch(r"(.+)≠0", normalized)
    if not match:
        return True

    left_side = match.group(1)

    # Remove useless conditions like 4 ≠ 0, 25/4 ≠ 0, 2(1) ≠ 0.
    return is_variable_dependent_denominator(left_side)

def infer_conditions_from_text(*texts) -> list:
    """
    Infers basic denominator restrictions from final answers/explanations.
    Example:
        x = 1 + z/y -> y ≠ 0
        x = \\frac{z}{y} -> y ≠ 0
    """
    joined = " ".join(str(t) for t in texts if t)
    if not joined:
        return []

    conditions = []

    # LaTeX fractions: \frac{z}{y}
    latex_denominators = re.findall(r"\\frac\{[^{}]+\}\{([^{}]+)\}", joined)
    for denominator in latex_denominators:
        denominator = denominator.strip()
        if is_variable_dependent_denominator(denominator):
            conditions.append(f"{denominator} ≠ 0")

    # Plain slash fractions: z/y or (y+z)/y
    plain_denominators = re.findall(r"/\s*([a-zA-Z][a-zA-Z0-9_]*)", joined)
    for denominator in plain_denominators:
        denominator = denominator.strip()
        if is_variable_dependent_denominator(denominator):
            conditions.append(f"{denominator} ≠ 0") 

    # Deduplicate while preserving order.
    unique_conditions = []
    for condition in conditions:
        normalized = normalize_condition(condition)
        if normalized not in unique_conditions:
            unique_conditions.append(normalized)

    return unique_conditions


def extract_final_answer_from_text(text: str) -> str:
    """
    Fallback extractor for final answer from plain explanation text.
    """
    if not text:
        return ""

    boxed_match = re.search(r"\\boxed\{([^{}]+)\}", text)
    if boxed_match:
        return boxed_match.group(1).strip()

    patterns = [
        r"final answer is\s*:?\s*(.+)",
        r"answer is\s*:?\s*(.+)",
        r"therefore,?\s*(.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            answer = match.group(1).strip()
            answer = answer.splitlines()[0].strip()
            answer = answer.strip("*` ")
            return answer

    return ""


def generate_simple_verification(problem: str, final_answer: str) -> list:
    """
    Generates a clean substitution verification for the common example:
    y(x - 1) = z, solve for x.
    For other problems, the verifier/explainer should provide verification.
    """
    compact_problem = re.sub(r"\s+", "", str(problem).lower())
    compact_answer = re.sub(r"\s+", "", str(final_answer).lower())

    is_y_problem = "y(x-1)=z" in compact_problem
    has_expected_answer = (
        "1+\\frac{z}{y}" in compact_answer
        or "1+z/y" in compact_answer
        or "\\frac{y+z}{y}" in compact_answer
        or "(y+z)/y" in compact_answer
    )

    if is_y_problem and has_expected_answer:
        return [
            r"y\left(\left(1 + \frac{z}{y}\right) - 1\right)",
            r"= y\left(\frac{z}{y}\right)",
            r"= z",
        ]

    return []


def build_solution_from_state(state: dict) -> dict:
    """
    Converts the workflow state into a consistent display format.
    Supports both structured JSON output and older plain markdown output.
    """
    raw_explanation = state.get("explanation", "")
    parsed_solution = safe_parse_solution(raw_explanation) or {}

    problem = (
        parsed_solution.get("problem")
        or state.get("parsed_problem")
        or st.session_state.raw_input
        or ""
    )

    final_answer = (
        parsed_solution.get("final_answer")
        or state.get("final_answer")
        or extract_final_answer_from_text(raw_explanation)
        or ""
    )

    explanation = (
        parsed_solution.get("explanation")
        or raw_explanation
        or ""
    )

    explanation = sanitize_user_facing_text(explanation)
    explanation = strip_duplicate_solution_headings(explanation)

    conditions = coerce_to_list(parsed_solution.get("conditions"))
    inferred_conditions = infer_conditions_from_text(final_answer, explanation)

    all_conditions = []
    for condition in conditions + inferred_conditions:
        normalized = normalize_condition(condition)
        if normalized and normalized not in all_conditions:
            all_conditions.append(normalized)

    steps = parsed_solution.get("steps") or []

    verification = coerce_to_list(
        parsed_solution.get("verification")
        or parsed_solution.get("verification_steps")
        or state.get("verification")
        or ""
    )

    if not verification:
        verification = generate_simple_verification(problem, final_answer)

    verifier_critique = sanitize_user_facing_text(state.get("verifier_critique", ""))

    return {
        "problem": problem,
        "final_answer": final_answer,
        "conditions": all_conditions,
        "steps": steps,
        "explanation": explanation,
        "verification": verification,
        "verifier_critique": verifier_critique,
        "topic": state.get("topic", ""),
        "is_verified": state.get("is_verified", None),
    }


# -----------------------------
# Rendering
# -----------------------------

def render_conditions(conditions: list):
    if not conditions:
        return

    st.markdown("### Conditions")

    condition_html = ""
    for condition in conditions:
        condition_html += f'<span class="condition-pill">{condition}</span>'

    st.markdown(condition_html, unsafe_allow_html=True)


def render_steps(steps: list, fallback_explanation: str = ""):
    if steps:
        for idx, step in enumerate(steps, start=1):
            if isinstance(step, dict):
                title = step.get("title") or f"Step {idx}"
                text = step.get("text", "")
                math_content = step.get("math", "")
            else:
                title = f"Step {idx}"
                text = str(step)
                math_content = ""

            st.markdown(
                f'<div class="step-title">Step {idx}: {title}</div>',
                unsafe_allow_html=True,
            )

            if text:
                st.markdown(sanitize_user_facing_text(text))

            if math_content:
                if isinstance(math_content, list):
                    for math_line in math_content:
                        render_math_or_text(math_line, force_math=True)
                else:
                    render_math_or_text(math_content, force_math=True)

    elif fallback_explanation:
        cleaned_explanation = sanitize_user_facing_text(fallback_explanation)
        cleaned_explanation = strip_duplicate_solution_headings(cleaned_explanation)
        st.markdown(cleaned_explanation)
    else:
        st.markdown(
            '<p class="muted-text">No step-by-step explanation was returned.</p>',
            unsafe_allow_html=True,
        )



def render_verification(verification: list, verifier_critique: str = "", is_verified=None):
    if not verification and not verifier_critique and is_verified is None:
        return

    st.markdown("### Verification")

    if verification:
        st.markdown("Substitute the final answer into the original problem:")

        for line in verification:
            render_math_or_text(line, force_math=True)

        if is_verified is False:
            st.warning("The verifier flagged this solution for review.")
        else:
            st.success("The substitution verifies the answer.")

    elif verifier_critique:
        st.markdown(verifier_critique)

    elif is_verified is True:
        st.success("The verifier marked this answer as correct.")
    elif is_verified is False:
        st.warning("The verifier marked this answer as incorrect or incomplete.")


def render_math_solution_card(solution: dict):
    problem = solution.get("problem", "")
    final_answer = solution.get("final_answer", "")
    conditions = solution.get("conditions", [])
    steps = solution.get("steps", [])
    explanation = solution.get("explanation", "")
    verification = solution.get("verification", [])
    verifier_critique = solution.get("verifier_critique", "")
    topic = solution.get("topic", "")
    is_verified = solution.get("is_verified", None)

    st.markdown('<div class="output-eyebrow">Result</div>', unsafe_allow_html=True)
    st.markdown('<div class="clean-section-title">Final Answer</div>', unsafe_allow_html=True)

    if final_answer:
        render_math_or_text(final_answer, force_math=True)
    else:
        st.markdown(
            '<p class="muted-text">No final answer was returned by the solver.</p>',
            unsafe_allow_html=True,
        )

    if topic:
        st.markdown(
            f'<p class="muted-text">Topic: {topic}</p>',
            unsafe_allow_html=True,
        )

    if conditions:
        st.markdown('<div class="clean-subtitle">Conditions</div>', unsafe_allow_html=True)
        condition_html = " ".join(
            [f'<span class="condition-pill">{condition}</span>' for condition in conditions]
        )
        st.markdown(condition_html, unsafe_allow_html=True)

    if problem:
        st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="clean-section-title">Given Problem</div>', unsafe_allow_html=True)

        if is_natural_language_prompt(problem):
            st.markdown(f"**{problem}**")
        else:
            render_math_or_text(problem)

    st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="clean-section-title">Solution Walkthrough</div>', unsafe_allow_html=True)

    render_steps(steps, fallback_explanation=explanation)

    should_show_verification = bool(verification) or bool(verifier_critique) or is_verified is not None

    if should_show_verification:
        st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="clean-section-title">Verification</div>', unsafe_allow_html=True)

        if verification:
            st.markdown("Substitute/check the final answer against the original problem:")

            for line in verification:
                render_math_or_text(line, force_math=True)

        if verifier_critique:
            st.markdown(verifier_critique)

        if is_verified is True:
            st.markdown(
                '<p class="success-text">The verifier marked this answer as correct.</p>',
                unsafe_allow_html=True,
            )
        elif is_verified is False:
            st.markdown(
                '<p class="warning-text">The verifier marked this answer as incorrect or incomplete.</p>',
                unsafe_allow_html=True,
            )



def render_developer_logs():
    if os.getenv("DEV_MODE", "false").lower() != "true":
        return

    if not st.session_state.agent_traces:
        return

    st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)

    with st.expander("View Developer Execution Logs"):
        for step_name, step_data in st.session_state.agent_traces:
            st.markdown(f"**Step:** `{step_name}`")
            st.json(step_data)



# -----------------------------
# Feedback
# -----------------------------

def save_feedback(state: dict, user_feedback: str, feedback_comment: str = ""):
    save_interaction(
        {
            "raw_input": st.session_state.raw_input,
            "parsed_question": state.get("parsed_problem", ""),
            "topic": state.get("topic", ""),
            "retrieved_context": state.get("retrieved_context", ""),
            "final_answer": state.get("final_answer", ""),
            "verifier_outcome": str(state.get("is_verified", user_feedback == "correct")),
            "user_feedback": user_feedback,
            "feedback_comment": feedback_comment,
        }
    )


def render_feedback_section(state: dict):
    st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="clean-section-title">Was this explanation helpful and correct?</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ Correct", key="feedback_correct"):
            save_feedback(state, user_feedback="correct")
            st.session_state.feedback_message = "Feedback saved. We’ll use it to improve future answers."
            st.session_state.show_error_report = False

    with col2:
        if st.button("❌ Incorrect", key="feedback_incorrect"):
            st.session_state.show_error_report = True
            st.session_state.feedback_message = ""

    if st.session_state.show_error_report:
        comment = st.text_area(
            "Please tell us what went wrong:",
            key="incorrect_feedback_comment",
            height=90,
        )

        if st.button("Submit Error Report", key="submit_error_report"):
            save_feedback(
                state,
                user_feedback="incorrect",
                feedback_comment=comment,
            )
            st.session_state.feedback_message = "Error report saved. We’ll use it to improve future answers."
            st.session_state.show_error_report = False

    if st.session_state.feedback_message:
        st.markdown(
            f'<p class="success-text">{st.session_state.feedback_message}</p>',
            unsafe_allow_html=True,
        )




# -----------------------------
# Chat-Style Sidebar History
# -----------------------------

def make_chat_title(problem: str) -> str:
    """
    Creates a short ChatGPT-style title from the user's math problem.
    """
    if not problem:
        return "New math problem"

    title = re.sub(r"\s+", " ", str(problem)).strip()

    title = re.sub(
        r"^(solve|find|calculate|differentiate|integrate|simplify)\s*:?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    )

    if len(title) > 42:
        title = title[:39].rstrip() + "..."

    return title or "New math problem"


def save_chat_snapshot(state: dict):
    """
    Saves the current solved problem into a clickable local sidebar history.
    This is frontend/session based and does not change the backend memory system.
    """
    if not isinstance(state, dict):
        return

    if st.session_state.workflow_error:
        return

    if not state.get("explanation") and not state.get("final_answer"):
        return

    problem = st.session_state.raw_input.strip()

    if not problem:
        return

    final_answer = str(state.get("final_answer", "")).strip()
    chat_key = f"{problem}::{final_answer}"

    if st.session_state.last_saved_chat_key == chat_key:
        return

    for item in st.session_state.chat_history_items:
        if item["key"] == chat_key:
            st.session_state.active_chat_id = item["id"]
            st.session_state.last_saved_chat_key = chat_key
            return

    chat_id = f"chat_{len(st.session_state.chat_history_items) + 1}_{abs(hash(chat_key))}"

    st.session_state.chat_history_items.insert(
        0,
        {
            "id": chat_id,
            "key": chat_key,
            "title": make_chat_title(problem),
            "problem": problem,
            "state": state.copy(),
        },
    )

    st.session_state.chat_history_items = st.session_state.chat_history_items[:12]
    st.session_state.active_chat_id = chat_id
    st.session_state.last_saved_chat_key = chat_key


def render_chat_history_sidebar():
    """
    Renders a clean ChatGPT-style sidebar instead of showing full solutions.
    """
    st.sidebar.markdown(
        """
        <div class="sidebar-header">
            <div class="sidebar-title">Math Mentor</div>
            <div class="sidebar-subtitle">Recent chats</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.chat_history_items:
        st.sidebar.markdown(
            """
            <div class="no-history-text">No history yet.</div>
            """,
            unsafe_allow_html=True,
        )
        return

    for item in st.session_state.chat_history_items:
        is_active = item["id"] == st.session_state.active_chat_id
        label = f"● {item['title']}" if is_active else item["title"]

        if st.sidebar.button(
            label,
            key=f"history_button_{item['id']}",
            use_container_width=True,
        ):
            st.session_state.raw_input = item["problem"]
            st.session_state.workflow_state = item["state"]
            st.session_state.workflow_error = ""
            st.session_state.input_processed = False
            st.session_state.active_chat_id = item["id"]
            st.rerun()

    st.sidebar.markdown(
        """
        <div class="history-footer">
            Click a chat title to reopen the full solution.
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Main App
# -----------------------------

def main():
    st.set_page_config(page_title="Math Mentor", page_icon="🧮", layout="wide")
    inject_custom_css()
    init_session()

    if isinstance(st.session_state.workflow_state, dict):
        save_chat_snapshot(st.session_state.workflow_state)

    render_chat_history_sidebar()

    st.markdown(
        """
        <div class="app-hero">
            <div class="hero-badge">AI Math Solver • Text • Image • Audio</div>
            <div class="hero-title">🧮 Multimodal Math Mentor</div>
            <div class="hero-subtitle">
                Solve math problems with clear final answers, step-by-step explanations,
                verification, and support for typed questions, screenshots, and spoken input.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="input-label">Choose Input Type</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Input Mode",
        ["Text", "Image", "Audio"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if input_mode == "Text":
        user_text = st.text_area("Type your math problem here:", height=140)

        if st.button("Submit Text"):
            if user_text.strip():
                st.session_state.raw_input = user_text
                st.session_state.input_processed = False
                st.session_state.workflow_state = None
                st.session_state.workflow_error = ""
                st.session_state.feedback_message = ""
                st.session_state.show_error_report = False

                run_agents(user_text)
                st.rerun()
            else:
                st.markdown(
                    '<p class="warning-text">Please enter some text.</p>',
                    unsafe_allow_html=True,
                )

    elif input_mode == "Image":
        uploaded_image = st.file_uploader(
            "Upload an image (photo or screenshot)",
            type=["png", "jpg", "jpeg"],
        )

        if uploaded_image is not None:
            st.image(uploaded_image, caption="Uploaded Image", width=400)

            if st.button("Extract Text"):
                with st.spinner("Extracting text via OCR..."):
                    extracted = parse_image(uploaded_image.getvalue())
                    st.session_state.raw_input = extracted
                    st.session_state.input_processed = True
                    st.session_state.workflow_state = None
                    st.session_state.workflow_error = ""
                    st.session_state.feedback_message = ""
                    st.session_state.show_error_report = False
                    st.rerun()

    elif input_mode == "Audio":
        uploaded_audio = st.file_uploader(
            "Upload an audio file spoken math question",
            type=["wav", "mp3", "m4a"],
        )

        if uploaded_audio is not None:
            st.audio(uploaded_audio)

            if st.button("Transcribe Audio"):
                with st.spinner("Transcribing..."):
                    transcript = parse_audio(uploaded_audio.getvalue(), filename=uploaded_audio.name)
                    st.session_state.raw_input = transcript
                    st.session_state.input_processed = True
                    st.session_state.workflow_state = None
                    st.session_state.workflow_error = ""
                    st.session_state.feedback_message = ""
                    st.session_state.show_error_report = False
                    st.rerun()

    # Human-in-the-loop review only for OCR/ASR extracted inputs.
    if st.session_state.input_processed and not st.session_state.workflow_state:
        st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="clean-section-title">Review Extracted Problem</div>', unsafe_allow_html=True)

        edited_text = st.text_area(
            "Review and edit the extracted text if necessary:",
            value=st.session_state.raw_input,
            height=120,
        )

        if st.button("Confirm and Solve"):
            st.session_state.raw_input = edited_text
            st.session_state.input_processed = False
            st.session_state.workflow_state = None
            st.session_state.workflow_error = ""
            run_agents(edited_text)
            st.rerun()

    if st.session_state.workflow_error:
        st.markdown('<div class="clean-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <p class="warning-text">
                The solver workflow could not complete. Set DEV_MODE=true and open developer logs for technical details.
            </p>
            """,
            unsafe_allow_html=True,
        )
        render_developer_logs()

    # Output rendering
    if st.session_state.workflow_state:
        state = st.session_state.workflow_state

        if not isinstance(state, dict):
            st.markdown(
                '<p class="warning-text">The workflow returned an unexpected state format.</p>',
                unsafe_allow_html=True,
            )
            render_developer_logs()
            return

        if state.get("needs_clarification"):
            st.markdown(
                '<p class="warning-text">The Parser Agent requires more information or clarification.</p>',
                unsafe_allow_html=True,
            )

            clarification = st.text_input("Please provide clarification:")

            if st.button("Submit Clarification"):
                st.session_state.raw_input += f" [Clarification: {clarification}]"
                run_agents(st.session_state.raw_input)
                st.rerun()

        elif state.get("explanation") or state.get("final_answer"):
            solution = build_solution_from_state(state)

            st.markdown('<div class="output-start"></div>', unsafe_allow_html=True)

            render_math_solution_card(solution)
            render_feedback_section(state)
            render_developer_logs()

        elif not st.session_state.workflow_error:
            st.markdown(
                '<p class="muted-text">The workflow completed, but no explanation or final answer was returned.</p>',
                unsafe_allow_html=True,
            )
            render_developer_logs()


if __name__ == "__main__":
    main()
