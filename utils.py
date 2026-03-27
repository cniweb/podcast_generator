import re
from typing import List


def _spell_out_abbreviations(text: str) -> str:
    """Expand 2-3 letter uppercase abbreviations (e.g., KI -> K I) for TTS clarity."""
    pattern = re.compile(r"(?<!#)\b([A-ZÄÖÜ]{2,3})\b")  # Hashtags ausnehmen
    stoplist = {
        "DER",
        "DIE",
        "DAS",
        "UND",
        "DEN",
        "DEM",
        "DES",
        "EIN",
        "EINE",
        "VON",
        "MIT",
        "AUS",
        "IM",
        "IN",
        "AM",
        "BEI",
        "AUF",
        "FÜR",
        "AN",
        "IST",
        "SIND",
        "ICH",
        "DU",
        "ER",
        "SIE",
        "ES",
        "WIR",
        "IHR",
    }

    def repl(match: re.Match) -> str:  # type: ignore[type-arg]
        word = match.group(1)
        if word in stoplist:
            return word
        return " ".join(list(word))

    return pattern.sub(repl, text)


def _strip_formatting(text: str) -> str:
    """Entfernt Markdown-Formatierungen und Sternchen-Betonung."""
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)  # Markdown-Link -> Text
    text = re.sub(r"\[\s*([^\]]+)\s*\]", r"\1", text)
    text = re.sub(r"\(\s*([^\)]+)\s*\)", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    return text


def _count_words(text: str) -> int:
    """Zählt Wort-Tokens (Whitespace-getrennt) nach Trimmen."""
    cleaned = " ".join(text.split())
    if not cleaned:
        return 0
    return len(cleaned.split(" "))


def _validate_script_constraints(
    text: str,
    min_words: int,
    max_words: int,
    min_paragraphs: int,
    expected_paragraphs: int | None = None,
) -> dict:
    """Validiert Sprechertext gegen Struktur- und Formatierungsregeln."""
    errors: list[str] = []
    forbidden_lines: list[str] = []

    heading_pattern = re.compile(r"^\s*[A-Za-zÄÖÜäöüß][\wÄÖÜäöüß\s]*:\s*$")
    divider_pattern = re.compile(r"^\s*-{3,}\s*$")
    bullet_pattern = re.compile(r"^\s*([-*]|\d+\.)\s+")
    stage_pattern = re.compile(
        r"\b(musik|jingle|sound|atmos|beat|lacht|faded)\b", re.IGNORECASE
    )

    found_heading = False
    found_divider = False
    found_bullet = False
    found_stage = False

    for line in text.splitlines():
        if not line.strip():
            continue
        if heading_pattern.match(line):
            found_heading = True
            if line not in forbidden_lines:
                forbidden_lines.append(line)
        if divider_pattern.match(line):
            found_divider = True
            if line not in forbidden_lines:
                forbidden_lines.append(line)
        if bullet_pattern.match(line):
            found_bullet = True
            if line not in forbidden_lines:
                forbidden_lines.append(line)
        if stage_pattern.search(line):
            found_stage = True
            if line not in forbidden_lines:
                forbidden_lines.append(line)

    if found_heading:
        errors.append("Überschriften/Labels gefunden.")
    if found_divider:
        errors.append("Trennerlinien gefunden.")
    if found_bullet:
        errors.append("Aufzählungen oder nummerierte Listen gefunden.")
    if found_stage:
        errors.append("Bühnenanweisungen/Stichworte gefunden.")

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    paragraph_count = len(paragraphs)
    word_count = _count_words(text)

    if word_count < min_words or word_count > max_words:
        errors.append(
            f"Wortanzahl außerhalb des Bereichs ({word_count} statt {min_words}-{max_words})."
        )
    if paragraph_count < min_paragraphs:
        errors.append(
            f"Zu wenige Absätze ({paragraph_count} statt mindestens {min_paragraphs})."
        )
    if expected_paragraphs is not None and paragraph_count != expected_paragraphs:
        errors.append(
            "Absatzanzahl entspricht nicht der erwarteten Struktur "
            f"({paragraph_count} statt {expected_paragraphs})."
        )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "word_count": word_count,
        "paragraph_count": paragraph_count,
        "forbidden_lines": forbidden_lines,
    }


def _chunk_text(text: str, max_chars: int = 1500) -> List[str]:
    """Zerteilt Text nach Absätzen, damit TTS-Limits eingehalten werden."""
    if max_chars <= 0:
        raise ValueError(
            f"max_chars muss eine positive Zahl sein, ist aber {max_chars!r}."
        )
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
