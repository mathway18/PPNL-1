"""Action parsing and normalization utilities."""

import re
from typing import List, Optional, Tuple

VALID_ACTIONS = {"up", "down", "left", "right"}
ACTION_RE = re.compile(r"\b(up|down|left|right)\b", flags=re.IGNORECASE)
FINAL_MARKER_RE = re.compile(r"\bfinal(?:\s+answer)?\s*[:\-]\s*", flags=re.IGNORECASE)


def normalize_action(token: str) -> Optional[str]:
    """Normalize a single token to a valid action, or return None."""
    token = token.strip().lower()
    if token in VALID_ACTIONS:
        return token
    return None


def _strip_markdown_fences(text: str) -> str:
    """Remove common markdown code-fence wrappers without touching content."""
    text = re.sub(r"```[a-zA-Z0-9_-]*", " ", text)
    text = text.replace("```", " ")
    return text.replace("`", " ")


def _select_action_segment(text: str) -> str:
    """Use the text after the last FINAL marker when one is present."""
    matches = list(FINAL_MARKER_RE.finditer(text))
    if matches:
        return text[matches[-1].end() :]
    return text


def parse_action_output(
    text: str,
    *,
    stop_at_invalid: bool = False,
) -> Tuple[str, List[str]]:
    """
    Parse a model output into a normalized action string and list.

    The parser is intentionally permissive for API outputs: it lowercases text,
    ignores markdown fences, prefers the content after the last ``FINAL:`` or
    ``Final answer:`` marker, and extracts only valid action words from text
    containing punctuation, arrows, brackets, or short labels.
    """
    if not text or not str(text).strip():
        return "", []

    cleaned = _strip_markdown_fences(str(text)).lower()
    cleaned = _select_action_segment(cleaned)
    cleaned = re.sub(r"[-=]+>", " ", cleaned)
    cleaned = re.sub(r"[-–—]+", " ", cleaned)
    cleaned = re.sub(r"[,\.;:\|\[\]\{\}\(\)\"'!?/\\]+", " ", cleaned)

    if stop_at_invalid:
        actions = []
        for token in cleaned.split():
            normalized = normalize_action(token)
            if normalized is None:
                if actions:
                    break
                continue
            actions.append(normalized)
    else:
        actions = [match.group(1).lower() for match in ACTION_RE.finditer(cleaned)]

    return " ".join(actions), actions


def extract_actions(text: str) -> Optional[List[str]]:
    """
    Extract a valid action sequence from free-form model output.

    Strategy:
    1. Prefer content after the last FINAL marker, if present.
    2. Find valid action tokens while ignoring punctuation/extra text.
    3. Return None if no valid actions found.
    """
    _, actions = parse_action_output(text)
    return actions if actions else None


def actions_to_str(actions: List[str]) -> str:
    """Convert a list of actions to a space-separated string."""
    return " ".join(actions)


def str_to_actions(s: str) -> Optional[List[str]]:
    """Parse a space-separated action string. Returns None if any token is invalid."""
    if not s or not s.strip():
        return None
    tokens = s.strip().split()
    result = []
    for tok in tokens:
        if tok not in VALID_ACTIONS:
            return None
        result.append(tok)
    return result if result else None
