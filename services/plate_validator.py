"""
Normalizes raw OCR text into a canonical plate string, and provides
edit-distance-tolerant matching so minor OCR mistakes (a tilted/partially
obscured plate) don't automatically fail a lookup.
"""
import re

from backend.config import OCR_CHAR_CORRECTIONS, PLATE_FUZZY_MAX_EDITS

_ALNUM_RE = re.compile(r"[^A-Z0-9]")
# Loose Indian plate shape: 2 letters, 1-2 digits, 1-3 letters, 4 digits
_PLATE_SHAPE_RE = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$")


def normalize_plate(raw_text: str) -> str:
    """Uppercase, strip spaces/hyphens/symbols. 'TN 09 AB-1234' -> 'TN09AB1234'."""
    text = raw_text.upper().strip()
    text = _ALNUM_RE.sub("", text)
    return text


def looks_like_plate(text: str) -> bool:
    """True if the normalized text matches a plausible plate shape."""
    if not (8 <= len(text) <= 11):
        return False
    return bool(_PLATE_SHAPE_RE.match(text)) or _mostly_alnum_mixed(text)


def _mostly_alnum_mixed(text: str) -> bool:
    """Fallback heuristic: has both letters and digits, no spaces, plausible length."""
    has_letter = any(c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)
    return has_letter and has_digit


def levenshtein(a: str, b: str) -> int:
    """Standard edit distance (insert/delete/substitute), used for fuzzy plate matching."""
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr_row = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr_row[j] = min(
                prev_row[j] + 1,        # deletion
                curr_row[j - 1] + 1,    # insertion
                prev_row[j - 1] + cost,  # substitution
            )
        prev_row = curr_row
    return prev_row[-1]


def generate_ocr_correction_variants(text: str):
    """
    Yields the original text plus variants where common OCR-confused
    characters (O<->0, I<->1, etc.) are swapped, to recover from
    misreads without needing a second OCR pass.
    """
    yield text
    chars = list(text)
    for i, c in enumerate(chars):
        if c in OCR_CHAR_CORRECTIONS:
            variant = chars.copy()
            variant[i] = OCR_CHAR_CORRECTIONS[c]
            yield "".join(variant)


def best_fuzzy_match(candidate: str, known_plates: list[str]):
    """
    Returns (matched_plate, edit_distance) for the closest known plate
    within PLATE_FUZZY_MAX_EDITS, or (None, None) if nothing is close enough.
    """
    best_plate, best_dist = None, None
    for known in known_plates:
        dist = levenshtein(candidate, known)
        if dist <= PLATE_FUZZY_MAX_EDITS and (best_dist is None or dist < best_dist):
            best_plate, best_dist = known, dist
    return best_plate, best_dist
