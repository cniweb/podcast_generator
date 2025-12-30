import re
from typing import List


def _spell_out_abbreviations(text: str) -> str:
    """Expand 2-3 letter uppercase abbreviations (e.g., KI -> K I) for TTS clarity."""
    pattern = re.compile(r"(?<!#)\b([A-ZÄÖÜ]{2,3})\b")
    stoplist = {
        "DER", "DIE", "DAS", "UND", "DEN", "DEM", "DES", "EIN", "EINE",
        "VON", "MIT", "AUS", "IM", "IN", "AM", "BEI", "AUF", "FÜR", "AN",
        "IST", "SIND", "ICH", "DU", "ER", "SIE", "ES", "WIR", "IHR",
    }

    def repl(match: re.Match) -> str:  # type: ignore[type-arg]
        word = match.group(1)
        if word in stoplist:
            return word
        return " ".join(list(word))

    return pattern.sub(repl, text)


def _strip_formatting(text: str) -> str:
    """
    Entfernt Markdown-Formatierungen und Sternchen-Betonung.
    """
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # Markdown Link -> Text
    text = re.sub(r"\[\s*([^\]]+)\s*\]", r"\1", text)
    text = re.sub(r"\(\s*([^\)]+)\s*\)", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text


def _chunk_text(text: str, max_chars: int = 1500) -> List[str]:
    """Chunk text to respect TTS limits, splitting by paragraphs."""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks = []
    current: List[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        # Wenn ein einzelner Paragraph zu lang ist, teilen wir ihn in Stücke
        if para_len > max_chars:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0

            start = 0
            while start < para_len:
                end = start + max_chars
                chunks.append(para[start:end])
                start = end
            continue

        if current_len + para_len + 2 <= max_chars:
            current.append(para)
            current_len += para_len + 2
        else:
            if current:
                chunks.append("\n\n".join(current))
            current = [para]
            current_len = para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks