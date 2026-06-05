import os
import base64
import requests
from groq import Groq
import tempfile
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import GraphState, get_llm
import re
import json


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def parse_image(image_bytes: bytes) -> str:
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "apikey": os.getenv("OCR_SPACE_API_KEY", "helloworld"),
            "language": "eng",
            "base64Image": f"data:image/jpeg;base64,{base64_image}",
            "OCREngine": "2",
        }

        res = requests.post("https://api.ocr.space/parse/image", data=payload, timeout=45)
        res_json = res.json()

        if res_json.get("IsErroredOnProcessing"):
            err = res_json.get("ErrorMessage", ["Unknown Error"])
            return f"Error from OCR API: {err}"

        results = res_json.get("ParsedResults", [])
        if not results:
            return "Could not extract any text. The image might be unreadable."

        parsed_text = results[0].get("ParsedText", "")
        return parsed_text.strip()

    except Exception as e:
        return f"Error using image parser: {str(e)}"


def parse_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    client = get_groq_client()
    if not client:
        return "Error: GROQ_API_KEY not set."

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=f"_{filename}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(filename or "audio.wav", audio_file),
                response_format="text",
            )

        return str(transcript).strip()

    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def _extract_json_object(text: str):
    if not text:
        return None

    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

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


def parser_node(state: GraphState):
    llm = get_llm()
    raw_input = state.get("raw_input", "")

    prompt = f"""
Convert this raw OCR/ASR/text input into a clean math problem or math question.

Return ONLY a valid JSON object with exactly these keys:
- problem_text
- topic
- variables
- constraints
- needs_clarification

Rules:
1. If the input is a normal math question, set needs_clarification to false.
2. Set needs_clarification to true only if the input is meaningless gibberish.
3. Do not output markdown.
4. variables and constraints may be strings or lists.

Raw Input:
{raw_input}
"""

    try:
        response = llm.invoke(
            [
                SystemMessage(content="You are a JSON math parser. Output only pure JSON."),
                HumanMessage(content=prompt),
            ]
        )

        parsed = _extract_json_object(response.content)

        if parsed is None:
            raise ValueError("Parser did not return valid JSON.")

    except Exception as e:
        print(f"JSON parsing failed, using fallback: {e}")
        parsed = {
            "problem_text": raw_input,
            "topic": "general math",
            "variables": "None",
            "constraints": "None",
            "needs_clarification": False,
        }

    needs_clarification = parsed.get("needs_clarification", False)
    if isinstance(needs_clarification, str):
        needs_clarification = needs_clarification.strip().lower() == "true"

    return {
        "parsed_problem": str(parsed.get("problem_text", raw_input)).strip(),
        "topic": str(parsed.get("topic", "general math")).strip(),
        "variables": parsed.get("variables", "None"),
        "constraints": parsed.get("constraints", "None"),
        "needs_clarification": bool(needs_clarification),
    }
