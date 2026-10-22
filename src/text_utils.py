"""Small, reusable text helpers.

Kept in src/ (not inside a notebook) so that the phase-1 text audit and the
phase-2 preprocessing use exactly the same cleaning rules.
"""

import html
import re

VIDEO_CODE = re.compile(r"\[\[VIDEOID:[^\]]*\]\]")
HTML_TAG = re.compile(r"<[a-zA-Z/][^>]*>")
WHITESPACE = re.compile(r"\s+")
WORD = re.compile(r"[A-Za-z']+")


def clean_text(text):
    """Remove markup that is not customer language.

    - embedded video codes like [[VIDEOID:abc123]]
    - HTML tags like <br /> (replaced by a space so words do not merge)
    - HTML entities like &amp; (decoded to the real character)
    - repeated whitespace
    """
    if text is None:
        return ""
    text = VIDEO_CODE.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    text = html.unescape(text)
    return WHITESPACE.sub(" ", text).strip()


def word_count(text):
    """Number of Latin-alphabet words (a simple, language-agnostic proxy)."""
    return len(WORD.findall(text or ""))


def script_of(text):
    """Rough writing-system label based on the letters in the text."""
    letters = [ch for ch in (text or "") if ch.isalpha()]
    if not letters:
        return "no letters"
    ranges = {
        "latin": lambda c: c < "ɐ",
        "cyrillic": lambda c: "Ѐ" <= c <= "ӿ",
        "arabic": lambda c: "؀" <= c <= "ۿ",
        "cjk": lambda c: "぀" <= c <= "鿿" or "가" <= c <= "힯",
    }
    counts = {name: sum(1 for c in letters if test(c)) for name, test in ranges.items()}
    best = max(counts, key=counts.get)
    return best if counts[best] / len(letters) >= 0.5 else "other/mixed"
