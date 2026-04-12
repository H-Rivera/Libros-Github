#!/usr/bin/env python3
"""
split_48_leyes.py — Divide '48 leyes del Poder' en un .md por ley
dentro de index/48-leyes-del-poder/

Usage:
    python scripts/split_48_leyes.py
"""

import pathlib
import re
from datetime import date

REPO_ROOT = pathlib.Path(__file__).parent.parent
DOCX_PATH = REPO_ROOT / "[PD] Libros - 48 leyes del Poder.docx"
OUT_DIR = REPO_ROOT / "index" / "48-leyes-del-poder"

# Noise patterns to skip
_NOISE = [
    re.compile(r'^LEY\s+N[°º\?\s\d]+[I\/\|]\s*\d+$'),   # "LEY N° 1 I 31"
    re.compile(r'^\d+\s*[I\/\|1]\s*LEY'),                 # "30 I LEY N°..."
    re.compile(r'^LEY\s+N[°º\?\.]\s*\d+\s*$'),            # "LEY N°" sola
    re.compile(r'^LEY\s+N[°º\?\s]*$'),                    # "LEY N°" incompleta
    re.compile(r'^\d+$'),                                  # numeros solos
    re.compile(r'^[A-Z]\.\s*[A-Z]\.$'),                   # "R. G."
    re.compile(r'p[áa]gina\s+\d+', re.IGNORECASE),        # "página 29"
    re.compile(r'^\d+\s+[I\/\|]\s*\d+$'),                 # "36  | 2"
    re.compile(r'^[I\/\|\s]+$'),                           # solo pipes/espacios
]

def is_noise(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    for pattern in _NOISE:
        if pattern.search(t):
            return True
    return False


def extract_paragraphs():
    from docx import Document
    doc = Document(str(DOCX_PATH))
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]


def find_law_boundaries(paragraphs):
    """
    Find where each law starts. Laws start with a block of UPPERCASE title lines
    followed by 'CRITERIO'. Returns list of (law_num, title, start_index).
    """
    boundaries = []
    i = 0
    while i < len(paragraphs):
        # Look for 'CRITERIO' which always starts a law section
        if paragraphs[i].strip() == 'CRITERIO':
            # Look backwards for the title (uppercase lines just before CRITERIO)
            title_lines = []
            j = i - 1
            while j >= 0 and paragraphs[j].isupper() and len(paragraphs[j]) > 2:
                title_lines.insert(0, paragraphs[j])
                j -= 1

            if title_lines:
                title = " ".join(title_lines)
                law_num = len(boundaries) + 1
                boundaries.append((law_num, title, j + 1))
        i += 1

    return boundaries


def split_into_laws(paragraphs, boundaries):
    """Split paragraphs into per-law chunks."""
    laws = []
    for idx, (law_num, title, start) in enumerate(boundaries):
        end = boundaries[idx + 1][2] if idx + 1 < len(boundaries) else len(paragraphs)
        content = [p for p in paragraphs[start:end] if not is_noise(p)]
        laws.append((law_num, title, content))
    return laws


def render_law_md(law_num: int, title: str, paragraphs: list) -> str:
    today = date.today().isoformat()
    lines = []
    lines.append(f"# Ley {law_num}: {title}\n")
    lines.append(f"**Libro:** Las 48 Leyes del Poder — Robert Greene  ")
    lines.append(f"**Extraido:** {today}\n")
    lines.append("---\n")

    current_section = None
    SECTIONS = {"CRITERIO", "OBSERVANCIA DE LA LEY", "CLAVES PARA ALCANZAR EL PODER",
                "TRANSGRESION DE LA LEY", "TRANSGRESIÓN DE LA LEY", "INVALIDACION",
                "INVALIDACIÓN", "INTERPRETACION", "INTERPRETACIÓN"}

    for p in paragraphs:
        clean = p.strip()
        if not clean:
            continue
        if clean.upper() in SECTIONS or clean in SECTIONS:
            current_section = clean
            lines.append(f"\n## {clean}\n")
        else:
            lines.append(clean)
            lines.append("")

    return "\n".join(lines)


def main():
    print("Extrayendo texto del DOCX...")
    paragraphs = extract_paragraphs()
    print(f"  {len(paragraphs)} parrafos encontrados")

    print("Detectando leyes...")
    boundaries = find_law_boundaries(paragraphs)
    print(f"  {len(boundaries)} leyes detectadas")

    if not boundaries:
        print("[ERROR] No se detectaron leyes. Revisa el archivo.")
        return

    laws = split_into_laws(paragraphs, boundaries)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write index file
    index_lines = [
        "# Las 48 Leyes del Poder — Indice\n",
        "**Autor:** Robert Greene\n",
        "---\n",
    ]
    for law_num, title, _ in laws:
        filename = f"ley-{law_num:02d}.md"
        index_lines.append(f"- [{law_num}. {title}]({filename})")
    index_path = OUT_DIR / "README.md"
    index_path.write_text("\n".join(index_lines), encoding="utf-8")
    print(f"[OK]   README.md -> indice de {len(laws)} leyes")

    # Write one file per law
    for law_num, title, content in laws:
        filename = f"ley-{law_num:02d}.md"
        out_path = OUT_DIR / filename
        md = render_law_md(law_num, title, content)
        out_path.write_text(md, encoding="utf-8")
        size_kb = out_path.stat().st_size / 1024
        print(f"[OK]   {filename} — {title[:40]} ({size_kb:.1f} KB)")

    # Summary
    total = sum((OUT_DIR / f"ley-{n:02d}.md").stat().st_size for n, _, _ in laws)
    print(f"\nTotal: {len(laws)} archivos, {total/1024:.0f} KB")
    print(f"Carpeta: index/48-leyes-del-poder/")


if __name__ == "__main__":
    main()
