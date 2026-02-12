import streamlit as st

def run_hitl(extracted_text: str, source: str):
    """
    Runs the Human-in-the-Loop flow for user verification.

    Args:
        extracted_text (str): Text extracted from OCR/ASR
        source (str): Input source ("image" or "audio")

    Retunrs:
        str: User-verified clean text    
    """

    st.warning(
        f" ⚠️ Low confidence detected in {source} input. "
        "Please review and correct the question if needed."
    )

    # Editable text box
    verified_text = st.text_area(
        label="Verify or correct the extracted math problem:",
        value=extracted_text,
        height=150
    )

    # Confirmation button
    confirmed = st.button("✅Confirm and Continue")

    if confirmed:
        cleaned_text = verified_text.strip()

        if cleaned_text == "":
            st.error("Text cannot be empty. Please provide a valid question.")
            return None
        
        return cleaned_text
    
    # If user has not confirmed yet
    return None