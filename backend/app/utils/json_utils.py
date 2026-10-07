"""Helpers for parsing and coercing the JSON that AI models return."""
import json
import re

from app.utils.errors import MalformedAIResponseError

_FENCE_START = re.compile(r"^```[a-zA-Z0-9_-]*\s*")
_FENCE_END = re.compile(r"\s*```$")


def extract_json_object(text: str) -> dict:
    """Extract the first JSON object from model output, tolerating code fences and prose."""
    if not text or not text.strip():
        raise MalformedAIResponseError("The AI returned an empty response.")
    s = text.strip()
    if s.startswith("```"):
        s = _FENCE_START.sub("", s)
        s = _FENCE_END.sub("", s).strip()
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(s[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise MalformedAIResponseError("The AI response did not contain a valid JSON object.")


def as_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def as_str_list(value, *, split_commas: bool = True) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if split_commas and "," in value:
            parts = (p.strip() for p in value.split(","))
        else:
            parts = (value.strip(),)
        return [p for p in parts if p]
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            s = as_str(item)
            if s:
                out.append(s)
        return out
    s = as_str(value)
    return [s] if s else []
