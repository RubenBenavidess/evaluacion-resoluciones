# extraction.py
# ------------------------------------------------------------
# Rule-based extraction from the normalized text:
# - n_resolution + title
# - recitals (CONSIDERANDO → each "Que, ...")
# - resolutions (RESUELVE → article bodies; strip leading "- ")
# - final_provisions (DISPOSICIONES FINALES)
# - final_message (only "Dado en ..." paragraph)
# - signatures (RECTOR, SECRETARIA + optional certification message)
#
# Output dict matches your schema (with final_message):
# {
#   "n_resolution": str,
#   "title": str,
#   "recitals": [str],
#   "resolutions": [str],
#   "final_provisions": [str],
#   "final_message": str,
#   "signatures": [{"author": str, "role": str, "message": str}, ...]
# }
# ------------------------------------------------------------

import json
import re
from typing import Dict, List, Optional, Tuple

from preprocessing.normalization import get_clean_text

# ------------ Regexes (section markers and patterns) ------------

RX_RESOLUTION_LINE = re.compile(r'RESOLUCI[ÓO]N\s*:\s*(.+)', re.I)
RX_CONSIDERANDO = re.compile(r'\bCONSIDERANDO\s*:?', re.I)
RX_RESUELVE = re.compile(r'\bRESUELVE\s*:?', re.I)
RX_DISPOSICIONES = re.compile(r'\bDISPOSICIONES\s+FINALES\b', re.I)

# Recitals (each starts with "Que,")
RX_RECITAL_ITEM = re.compile(r'(?:^|\n)(Que,\s.*?)(?=(?:\nQue,|\n?RESUELVE\b|$))', re.I | re.S)

# Articles inside RESUELVE (capture body only)
# Swallow ". - " or ".-" right after the header so bodies don't start with "- "
RX_ARTICLE = re.compile(
    r'(?:^|\n)\s*(?:Art[íi]?culo|Art\.)\s*'
    r'(?:\d+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO|D[EÉ]CIMO)'
    r'\s*[.\-–—]+(?:\s*-\s*)?\s*(.*?)(?=(?:\n\s*(?:Art[íi]?culo|Art\.)\s*'
    r'(?:\d+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO|D[EÉ]CIMO)'
    r'\s*[.\-–—]+)|$)',
    re.I | re.S
)

# Final provisions (ordinal + text)
ORDINAL = r'(PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|S[EÉ]PTIMA|OCTAVA|NOVENA|D[EÉ]CIMA)'
RX_FINAL_ITEM = re.compile(
    rf'(?:^|\n)\s*{ORDINAL}\s*[\.\-–—]*\s*(.*?)(?=(?:\n\s*{ORDINAL}\s*[\.\-–—]*|$))',
    re.I | re.S
)

# Final message starts at "Dado en ..."
RX_FINAL_MESSAGE_START = re.compile(r'\bDado en\b', re.I)

# Signature blocks / roles (capture and keep prefix in author)
RX_RECTOR_SIG = re.compile(
    r'(?:(Mgtr\.|Msc\.|Ing\.|Abg\.|Lcd\.)\s+)?'   # optional academic prefix
    r'([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\.]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\.]+){1,4})\s+RECTOR\b',
    re.I
)

# Make courtesy prefix MANDATORY for SECRETARIA to avoid greedy captures
RX_SECRETARIA_SIG = re.compile(
    r'(Srta\.|Sra\.|Sr\.)\s+'                     # mandatory courtesy prefix
    r'([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\.]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ\.]+){1,5})\s+SECRETARIA\b',
    re.I
)

# Final message block: from "Dado en ..." up to BEFORE any signature/certification marker
RX_FINAL_MESSAGE_BLOCK = re.compile(
    r'(Dado en.*?)(?=\s*(?:[A-ZÁÉÍÓÚÑ]\.?\s+)?(?:Mgtr\.|Msc\.|Ing\.|Abg\.|Lcd\.|Srta\.|Sra\.|Sr\.|RECTOR|SECRETARIA|En mi calidad)\b|$)',
    re.I | re.S
)

# Secretaria certification message (keep it concise)
RX_CERTIFICO_BLOCK = re.compile(r'(En mi calidad.*?Lo certifico\.)', re.I | re.S)

# Boundaries that indicate the start of signatures after final message
FINAL_MSG_BOUNDARIES = [
    re.compile(r'\bMgtr\.\b', re.I),
    re.compile(r'\bMsc\.\b', re.I),
    re.compile(r'\bIng\.\b', re.I),
    re.compile(r'\bAbg\.\b', re.I),
    re.compile(r'\bLcd\.\b', re.I),
    re.compile(r'\bSrta\.\b', re.I),
    re.compile(r'\bSra\.\b', re.I),
    re.compile(r'\bSr\.\b', re.I),
    re.compile(r'\bRECTOR\b', re.I),
    re.compile(r'\bSECRETARIA\b', re.I),
    re.compile(r'\bCERTIFICO\b', re.I),
]

# -------------------------- Helpers ----------------------------

def _cleanup_line(s: str) -> str:
    """Basic whitespace and stray punctuation cleanup."""
    s = s.replace('  ', ' ')
    s = re.sub(r'\s+\.', '.', s)
    s = re.sub(r'\s+,', ',', s)
    s = re.sub(r'\s+;', ';', s)
    return s.strip()


def _find_between(text: str, start_rx: re.Pattern, end_rx: re.Pattern) -> str:
    """Return substring between start marker and next end marker; empty if not found."""
    start = start_rx.search(text)
    if not start:
        return ''
    start_idx = start.end()
    end = end_rx.search(text, start_idx)
    end_idx = end.start() if end else len(text)
    return text[start_idx:end_idx].strip()


def _before(text: str, end_rx: re.Pattern) -> str:
    """Return substring from start to the first occurrence of end_rx."""
    end = end_rx.search(text)
    return text[:end.start()].strip() if end else text.strip()


def _after(text: str, start_rx: re.Pattern) -> str:
    """Return substring from the end of start_rx to EOF."""
    start = start_rx.search(text)
    return text[start.end():].strip() if start else ''


def _earliest_index(s: str, patterns: List[re.Pattern]) -> Optional[int]:
    """Return earliest index in s where any pattern matches; None if no matches."""
    idxs = [m.start() for rx in patterns for m in [rx.search(s)] if m]
    return min(idxs) if idxs else None


# -------------------------- Extractors -------------------------

def extract_n_resolution(text: str) -> str:
    m = RX_RESOLUTION_LINE.search(text)
    if not m:
        return ''
    nres = m.group(1).strip()
    # Fix common spacing issue like "R- OCS" -> "R-OCS"
    nres = re.sub(r'R-\s+OCS', 'R-OCS', nres, flags=re.I)
    return _cleanup_line(nres)


def extract_title(text: str) -> str:
    # Title is the text after the "RESOLUCIÓN: ..." line until "CONSIDERANDO:"
    after_res = _after(text, RX_RESOLUTION_LINE)
    title_block = _before(after_res, RX_CONSIDERANDO)
    # Remove "CONSIDERANDO:" if stuck to the same line
    title_block = re.sub(r'\bCONSIDERANDO\s*:?\b', '', title_block, flags=re.I).strip()
    # Single line
    title_block = re.sub(r'\s+', ' ', title_block)
    return _cleanup_line(title_block)


def extract_recitals(text: str) -> List[str]:
    block = _find_between(text, RX_CONSIDERANDO, RX_RESUELVE)
    if not block:
        return []
    items = []
    for m in RX_RECITAL_ITEM.finditer('\n' + block):  # \n to unify anchors
        item = m.group(1).strip()
        items.append(_cleanup_line(item))
    return items


def extract_resolutions(text: str) -> List[str]:
    block = _find_between(text, RX_RESUELVE, RX_DISPOSICIONES)
    if not block:
        return []
    res = []
    for m in RX_ARTICLE.finditer('\n' + block):
        body = m.group(1).strip()
        # If a stray leading hyphen survived, remove it
        body = re.sub(r'^\s*-\s*', '', body)
        body = _cleanup_line(body)
        res.append(body)
    return res


def extract_final_provisions_and_message(text: str) -> Tuple[List[str], str]:
    disp_block = _after(text, RX_DISPOSICIONES)
    if not disp_block:
        return [], ''

    # --- Final message (clean block) ---
    final_msg = ''
    m_block = RX_FINAL_MESSAGE_BLOCK.search(disp_block)
    if m_block:
        final_msg = _cleanup_line(m_block.group(1).strip())
        # Cut EVERYTHING after the final message from the provisions area
        disp_block_wo_msg = disp_block[:m_block.start()]
    else:
        disp_block_wo_msg = disp_block

    # --- Final provisions from the remaining block ---
    provisions: List[str] = []
    for m in RX_FINAL_ITEM.finditer('\n' + disp_block_wo_msg):
        text_item = m.group(2).strip() if m.lastindex and m.lastindex >= 2 else m.group(0).strip()
        ordinal = m.group(1).upper()
        full = f"{ordinal}. {text_item}"
        provisions.append(_cleanup_line(full))

    if not provisions:
        parts = re.split(rf'(?=\b{ORDINAL}\b)', disp_block_wo_msg, flags=re.I)
        for p in parts:
            p = p.strip()
            if not p:
                continue
            if re.match(rf'^{ORDINAL}\b', p, flags=re.I):
                provisions.append(_cleanup_line(p))

    return provisions, final_msg

def extract_signatures(text: str) -> List[Dict[str, str]]:
    tail = _after(text, RX_DISPOSICIONES) or text

    rector_author = ''
    m_rector = RX_RECTOR_SIG.search(tail)
    if m_rector:
        prefix = (m_rector.group(1) or '').strip()
        name = _cleanup_line(m_rector.group(2).strip())
        rector_author = (prefix + ' ' + name).strip()

    m_secr = RX_SECRETARIA_SIG.search(tail)
    if m_secr:
        prefix = (m_secr.group(1) or '').strip()
        name = _cleanup_line(m_secr.group(2).strip())
        secretaria_author = (prefix + ' ' + name).strip()

    secretaria_msg = ''
    m_cert = RX_CERTIFICO_BLOCK.search(tail)
    if m_cert:
        secretaria_msg = _cleanup_line(m_cert.group(1).strip())

    signatures: List[Dict[str, str]] = []
    if rector_author:
        signatures.append({"author": rector_author, "role": "RECTOR", "message": ""})
    if secretaria_author or secretaria_msg:
        signatures.append({
            "author": secretaria_author or "",
            "role": "SECRETARIA",
            "message": secretaria_msg
        })

    if not signatures:
        signatures = [{"author": "", "role": "", "message": ""}, {"author": "", "role": "", "message": ""}]
    elif len(signatures) == 1:
        signatures.append({"author": "", "role": "", "message": ""})

    return signatures

# ----------------------- Public API ----------------------------

def extract_to_dict() -> Dict:
    """
    Run extraction on the normalized text and return a dict matching your JSON schema.
    """
    text = get_clean_text()

    data = {
        "n_resolution": extract_n_resolution(text),
        "title": extract_title(text),
        "recitals": extract_recitals(text),
        "resolutions": extract_resolutions(text),
        "final_provisions": [],
        "final_message": "",
        "signatures": []
    }

    provisions, final_msg = extract_final_provisions_and_message(text)
    data["final_provisions"] = provisions
    data["final_message"] = final_msg
    data["signatures"] = extract_signatures(text)

    return data


def save_extraction_json(path: str) -> None:
    """Dump the extracted dict to a JSON file."""
    data = extract_to_dict()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
