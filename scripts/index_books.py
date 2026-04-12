#!/usr/bin/env python3
"""
index_books.py — Generate Markdown index files for books in the repo root.

Usage:
    python scripts/index_books.py                  # index all, skip existing
    python scripts/index_books.py --force           # re-index everything
    python scripts/index_books.py "BOOK.pdf"        # index single file
"""

import argparse
import pathlib
import re
import sys
from datetime import date

REPO_ROOT = pathlib.Path(__file__).parent.parent
INDEX_DIR = REPO_ROOT / "index"
SUPPORTED = {".pdf", ".docx", ".txt"}


# ─── Chapter Detection ────────────────────────────────────────────────────────

_HEADING_RE = re.compile(
    r'^(?:chapter\s+\d+[:\.\-]?\s*.{0,60}|part\s+\d+[:\.\-]?\s*.{0,60}|\d+[\.\)]\s+[A-Z].{3,50}|[A-Z][A-Z\s]{3,50})$',
    re.IGNORECASE
)

def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80 or line.endswith('.'):
        return False
    return bool(_HEADING_RE.match(line))

def detect_chapters(pages):
    if not pages:
        return []
    chapters = []
    current_title = None
    current_lines = []

    for page in pages:
        for line in page.splitlines():
            if _is_heading(line):
                if current_title is not None:
                    chapters.append({"title": current_title, "text": "\n".join(current_lines).strip()})
                current_title = line.strip()
                current_lines = []
            else:
                current_lines.append(line)

    if current_title is not None:
        chapters.append({"title": current_title, "text": "\n".join(current_lines).strip()})

    # fallback: group every 10 pages
    if not chapters:
        for i in range(0, len(pages), 10):
            chunk = pages[i:i + 10]
            chapters.append({
                "title": f"Pages {i+1}–{i+len(chunk)}",
                "text": "\n\n".join(chunk).strip()
            })
    return chapters


# ─── Extractors ───────────────────────────────────────────────────────────────

def extract_pdf(path):
    import fitz
    doc = fitz.open(str(path))
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    page_count = doc.page_count
    doc.close()
    return {"title": path.stem, "source": path.name, "page_count": page_count, "pages": pages}

def _clean_docx_paragraph(text: str) -> bool:
    """Return True if paragraph should be kept (not noise)."""
    t = text.strip()
    if not t:
        return False
    # Page numbers: "CONTENIDO I 9", "10 I CONTENIDO", "12  I CONTENIDO"
    if re.match(r'^[\w\s]+I\s+\d+$', t) or re.match(r'^\d+\s+I\s+[\w\s]+$', t):
        return False
    # Index entries with page refs: "LEY N° 1 página 29", "PREFACIO  página 19"
    if re.search(r'p[áa]gina\s+\d+', t, re.IGNORECASE):
        return False
    # Pure page numbers
    if re.match(r'^\d+$', t):
        return False
    # Very short noise (single initials like "R. G.", "J. E.")
    if re.match(r'^[A-Z]\.\s*[A-Z]\.$', t):
        return False
    # Repeated slash noise
    if re.match(r'^[/\|\\]+$', t):
        return False
    return True

def extract_docx(path):
    from docx import Document
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if _clean_docx_paragraph(p.text)]
    pages = []
    for i in range(0, len(paragraphs), 50):
        pages.append("\n".join(paragraphs[i:i + 50]))
    return {"title": path.stem, "source": path.name, "page_count": len(pages), "pages": pages}

def extract_txt(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    raw_pages = [p.strip() for p in text.split("\n\n") if p.strip()]
    pages = raw_pages if raw_pages else [text]
    return {"title": path.stem, "source": path.name, "page_count": len(pages), "pages": pages}

def extract_file(path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".docx":
        return extract_docx(path)
    elif ext == ".txt":
        return extract_txt(path)
    else:
        raise ValueError(f"Unsupported: {ext}")


# ─── Markdown Writer ──────────────────────────────────────────────────────────

def render_markdown(data):
    today = date.today().isoformat()
    chapters = data.get("chapters", [])
    lines = []

    lines.append(f"# {data['title']}\n")
    lines.append(f"**Source:** {data['source']}  ")
    lines.append(f"**Pages:** {data['page_count']}  ")
    lines.append(f"**Extracted:** {today}\n")
    lines.append("---\n")

    lines.append("## Table of Contents\n")
    for ch in chapters:
        lines.append(f"- {ch['title']}")
    lines.append("\n---\n")

    for ch in chapters:
        lines.append(f"## {ch['title']}\n")
        lines.append(ch["text"])
        lines.append("\n---\n")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def sanitize_name(stem):
    name = re.sub(r"\s+", "-", stem)
    name = re.sub(r"[^\w\-]", "", name)
    return name.strip("-")

def index_file(path, force=False):
    out_name = sanitize_name(path.stem) + ".md"
    out_path = INDEX_DIR / out_name

    if out_path.exists() and not force:
        print(f"[SKIP] {path.name} - ya indexado (usa --force para re-indexar)")
        return

    try:
        data = extract_file(path)
        chapters = detect_chapters(data["pages"])
        data["chapters"] = chapters
        md = render_markdown(data)
        INDEX_DIR.mkdir(exist_ok=True)
        out_path.write_text(md, encoding="utf-8", errors="replace")
        print(f"[OK]   {path.name} -> index/{out_name} ({data['page_count']} paginas, {len(chapters)} secciones)")
    except Exception as e:
        print(f"[FAIL] {path.name} - {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Archivo especifico a indexar")
    parser.add_argument("--force", action="store_true", help="Re-indexar aunque ya exista")
    args = parser.parse_args()

    if args.file:
        path = REPO_ROOT / args.file
        if not path.exists():
            print(f"[ERROR] No encontrado: {path}")
            sys.exit(1)
        index_file(path, force=args.force)
    else:
        files = sorted([f for f in REPO_ROOT.iterdir() if f.suffix.lower() in SUPPORTED])
        if not files:
            print("No se encontraron archivos soportados en la raiz del repo.")
            sys.exit(0)
        for f in files:
            index_file(f, force=args.force)

if __name__ == "__main__":
    main()
