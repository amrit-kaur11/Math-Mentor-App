from config.settings import(
   OCR_CONFIDENCE_THRESHOLD,
   ASR_CONFIDENCE_THRESHOLD 
)


def is_confidence_sufficient(confidence: float, source: str) -> bool:
    """
    Determines whether the confidence score is sufficient to proceed
    without Human-in-the-Loop intervention.

    Args:
        confidence (float): Confidence score(0.0 -1.0)
        score (str): Input source type ("text", "image", "audio")

    Returns:
        Bool: True if confidence is sufficient, else False    
    """
    if source == "text":
      # Typed text is always trusted 
      return True

    if source == "image":
       return confidence >= OCR_CONFIDENCE_THRESHOLD

    if source == "audio":
        return confidence >= ASR_CONFIDENCE_THRESHOLD

    # Unknown source → be safe
    return False
