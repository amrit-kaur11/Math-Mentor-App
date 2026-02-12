import streamlit as st

# ---------------- IMPORTS ---------------- #

from inputs.text_input import process_text
from inputs.image_input import process_image
from inputs.audio_input import process_audio

from inputs.confidence import is_confidence_sufficient
from hitl.hitl_handler import run_hitl

from memory.memory_store import initialize_memory, store_step1_record
from memory.parsed_store import initialize_parsed_memory, store_parsed_record

from parser.parser_agent import parse_math_question
from rag.retriever import retrieve
from solver.solver_agent import solve_math_problem
from solver.mock_llm import mock_llm
from verifier.verifier_agent import verify_equation


# ---------------- APP CONFIG ---------------- #

APP_TITLE = "Multimodal Math Mentor"

st.set_page_config(page_title=APP_TITLE, layout="centered")
st.title(APP_TITLE)

initialize_memory()
initialize_parsed_memory()

# ---------------- SESSION STATE INIT ---------------- #

if "verified_text" not in st.session_state:
    st.session_state.verified_text = None

if "pending_record" not in st.session_state:
    st.session_state.pending_record = None


# ---------------- STEP 1: INPUT ---------------- #

st.write("### Step 1: Multimodal Input & Validation")

input_mode = st.radio(
    "Select input type:",
    options=["Text", "Image", "Audio"]
)

extracted_text = None
confidence = 0.0
source = None
raw_input_ref = None

# -------- TEXT INPUT -------- #
if input_mode == "Text":
    user_text = st.text_area("Enter a math problem:")

    if st.button("Submit Text") and user_text:
        extracted_text, confidence = process_text(user_text)
        source = "text"
        raw_input_ref = "typed_input"

# -------- IMAGE INPUT -------- #
elif input_mode == "Image":
    image_file = st.file_uploader("Upload an image (JPG/PNG):", type=["jpg", "jpeg", "png"])

    if st.button("Process Image") and image_file:
        extracted_text, confidence = process_image(image_file)
        source = "image"
        raw_input_ref = image_file.name

# -------- AUDIO INPUT -------- #
elif input_mode == "Audio":
    audio_file = st.file_uploader("Upload an audio file:", type=["wav", "mp3"])

    if st.button("Process Audio") and audio_file:
        extracted_text, confidence = process_audio(audio_file)
        source = "audio"
        raw_input_ref = audio_file.name


# ---------------- HITL + STORE STEP 1 ---------------- #

if extracted_text:

    st.write("### Extracted Text:")
    st.code(extracted_text)

    verified_text = None
    hitl_used = False

    if not is_confidence_sufficient(confidence, source):
        st.warning("⚠ Low confidence detected. Please review and correct.")
        verified_text = run_hitl(extracted_text, source)
        hitl_used = True
    else:
        verified_text = extracted_text

    if verified_text:
        st.session_state.verified_text = verified_text

        store_step1_record(
            input_type=source,
            raw_input_ref=raw_input_ref,
            extracted_text=extracted_text,
            verified_text=verified_text,
            confidence=confidence,
            hitl_used=hitl_used
        )

        st.success("✅ Step 1 completed and stored.")


# ---------------- STEP 2 → STEP 5 PIPELINE ---------------- #

if st.session_state.verified_text:

    st.divider()
    st.write("## Step 2: Parsing")

    parsed_output = parse_math_question(
        st.session_state.verified_text
    )

    st.json(parsed_output)

    store_parsed_record(
        verified_text=st.session_state.verified_text,
        parsed_output=parsed_output
    )

    st.success("✅ Step 2 completed.")


    # ---------------- STEP 3: RETRIEVAL ---------------- #

    st.divider()
    st.write("## Step 3: Retrieval")

    retrieved_docs = retrieve(
        st.session_state.verified_text
    )

    st.write(retrieved_docs)


    # ---------------- STEP 4: SOLVER ---------------- #

    st.divider()
    st.write("## Step 4: Solution")

    solution = solve_math_problem(parsed_output)

    st.write(solution)


    # ---------------- STEP 5: VERIFIER ---------------- #

    st.divider()
    st.write("## Step 5: Verification")

    verification_result = verify_equation(
        st.session_state.verified_text,
        solution["final_answer"]
    )

    st.json(verification_result)

    if verification_result["verified"]:
        st.success("✔ Solution Verified")
    else:
        st.error("✖ Verification Failed")
