"""PDF -> structured circular: header metadata + numbered paragraphs + sentences.

Every downstream finding cites a paragraph reference ("Para 3", "Para 15.3.4")
and a page number, so obligations are always traceable to source text.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE_RE = re.compile(rf"\b({MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})\b", re.I)
_PAGE_LINE = re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.I)
_PARA_START = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){0,4})\.?\s+(?=\S)")
_CIRC_NO = re.compile(r"\b((?:SEBI/)?HO/[\w()/.\-\s]{6,80}?/\d{4})\b")
_ABBREV = re.compile(r"\b(No|Nos|Rs|viz|i\.e|e\.g|para|Para|Reg|Regn|Sr|Dr|Mr|Ms|w\.e\.f|etc|vs|cl)\.$")


@dataclass
class Paragraph:
    ref: str  # "Para 3" / "Para 15.3.4" / "Preamble"
    number: str | None
    page: int  # 1-based
    text: str
    sentences: list[str] = field(default_factory=list)


@dataclass
class ParsedCircular:
    circular_number: str | None
    date: str | None  # ISO yyyy-mm-dd
    addressees: list[str]
    subject: str | None
    paragraphs: list[Paragraph]
    full_text: str
    page_count: int
    text_hash: str

    @property
    def is_scanned(self) -> bool:
        return len(self.full_text.strip()) < 200


def to_iso(m: re.Match) -> str | None:
    from datetime import datetime

    try:
        return datetime.strptime(f"{m.group(1).title()} {int(m.group(2))} {m.group(3)}", "%B %d %Y").date().isoformat()
    except ValueError:
        return None


def split_sentences(text: str) -> list[str]:
    parts: list[str] = []
    buf = ""
    for tok in re.split(r"(?<=[.;:])\s+", text):
        buf = f"{buf} {tok}".strip() if buf else tok
        # don't split after abbreviations, numbering like "15.3." or short fragments
        if _ABBREV.search(buf) or re.search(r"\d\.$", buf) or len(buf) < 25:
            continue
        parts.append(buf.strip())
        buf = ""
    if buf.strip():
        if parts and len(buf) < 25:
            parts[-1] += " " + buf.strip()
        else:
            parts.append(buf.strip())
    return parts


def _clean(s: str) -> str:
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    s = s.replace("…", "...").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


def parse_pdf(path: str | Path) -> ParsedCircular:
    doc = fitz.open(str(path))
    lines: list[tuple[int, str]] = []
    for pno, page in enumerate(doc, start=1):
        for raw in page.get_text().splitlines():
            if _PAGE_LINE.match(raw) or not raw.strip():
                continue
            lines.append((pno, raw.rstrip()))
    page_count = len(doc)
    doc.close()
    return parse_lines(lines, page_count)


def parse_text(text: str) -> ParsedCircular:
    return parse_lines([(1, line) for line in text.splitlines() if line.strip()], 1)


def parse_lines(lines: list[tuple[int, str]], page_count: int) -> ParsedCircular:
    full_text = "\n".join(t for _, t in lines)
    text_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

    head = "\n".join(t for _, t in lines[:40])
    m = _CIRC_NO.search(head)
    circular_number = re.sub(r"\s+", "", m.group(1)) if m else None
    dm = DATE_RE.search(head)
    date = to_iso(dm) if dm else None

    # addressees: between "To," and the salutation
    addressees: list[str] = []
    in_to = False
    subject_lines: list[str] = []
    in_sub = False
    body_start = 0
    for i, (_, t) in enumerate(lines[:60]):
        s = t.strip()
        if re.match(r"^To\b,?", s):
            in_to = True
            continue
        if in_to:
            if re.search(r"(Madam|Sir|Dear)", s, re.I):
                in_to = False
            elif s:
                addressees.append(s.rstrip(",;"))
        if re.match(r"^Sub(ject)?\s*:", s, re.I):
            in_sub = True
            subject_lines.append(re.sub(r"^Sub(ject)?\s*:\s*", "", s, flags=re.I))
            continue
        if in_sub:
            if _PARA_START.match(s):
                in_sub = False
                body_start = i
                break
            subject_lines.append(s)
    subject = _clean(" ".join(subject_lines)) or None

    # paragraphs
    paragraphs: list[Paragraph] = []
    cur: Paragraph | None = None
    preamble: list[str] = []
    for pno, t in lines[body_start:]:
        s = t.strip()
        if re.match(r"^(Yours faithfully|Yours sincerely)", s, re.I):
            break
        pm = _PARA_START.match(s)
        # a wrapped line like "33 of SEBI (Research Analysts) Regulations" is not a new paragraph
        if pm and "." not in pm.group(1) and s[pm.end():pm.end() + 1].islower():
            pm = None
        if pm:
            if cur:
                paragraphs.append(cur)
            num = pm.group(1)
            cur = Paragraph(ref=f"Para {num}", number=num, page=pno, text=s[pm.end():])
        elif cur:
            cur.text += " " + s
        else:
            preamble.append(s)
    if cur:
        paragraphs.append(cur)
    if not paragraphs and preamble:
        paragraphs.append(Paragraph(ref="Body", number=None, page=1, text=" ".join(preamble)))

    for p in paragraphs:
        p.text = _clean(p.text)
        p.sentences = split_sentences(p.text)

    return ParsedCircular(
        circular_number=circular_number,
        date=date,
        addressees=addressees,
        subject=subject,
        paragraphs=paragraphs,
        full_text=_clean(full_text),
        page_count=page_count,
        text_hash=text_hash,
    )
