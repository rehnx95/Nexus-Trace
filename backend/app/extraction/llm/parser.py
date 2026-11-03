import json
import re


def parse_llm_json(content: str) -> dict:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1)
    elif text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^json\s*", "", text, flags=re.IGNORECASE)

    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("LLM output must be a JSON object")
    if not isinstance(payload.get("entities", []), list):
        raise ValueError("LLM entities must be a list")
    if not isinstance(payload.get("edges", []), list):
        raise ValueError("LLM edges must be a list")
    return payload
