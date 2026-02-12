import whisper


# Load model once (important for performance)
model = whisper.load_model("base")


def process_audio(audio_file_path: str):
    """
    Processes an audio file and converts speech to text.

    Args:
        audio_file_path (str): Path to the audio file

    Returns:
        tuple:
            - transcript (str)
            - confidence (float)
    """

    try:
        # Transcribe audio
        result = model.transcribe(audio_file_path)

        transcript = result.get("text", "").strip()

        if transcript == "":
            return None, 0.0

        # Whisper does not give explicit confidence,
        # so we use a heuristic confidence
        confidence = estimate_confidence(result)

        return transcript, confidence

    except Exception:
        return None, 0.0


def estimate_confidence(result: dict) -> float:
    """
    Estimate transcription confidence using heuristic.

    Args:
        result (dict): Whisper transcription result

    Returns:
        confidence (float)
    """

    segments = result.get("segments", [])

    if not segments:
        return 0.0

    # Use average log probability as proxy confidence
    log_probs = [seg.get("avg_logprob", -1.0) for seg in segments]

    avg_log_prob = sum(log_probs) / len(log_probs)

    # Normalize log prob into 0–1 range (simple heuristic)
    confidence = max(0.0, min(1.0, (avg_log_prob + 1)))

    return confidence
