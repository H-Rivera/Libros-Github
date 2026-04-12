# Book Indexer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate one structured Markdown file per book inside `/index/` so Claude Code can read any book's full text without processing original PDFs each session.

**Architecture:** A single Python script scans the repo root for PDF/DOCX/TXT files, extracts and structures the text by chapter (with page-based fallback), and writes one `.md` per book to the `/index/` folder. Supports `--force` to re-index and single-file targeting.

**Tech Stack:** Python 3.8+, `pymupdf` (PDF extraction), `python-docx` (DOCX extraction), stdlib only otherwise.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `scripts/index_books.py` | Main script: scan, extract, write |
| Create | `scripts/extractors.py` | Per-format text extraction (PDF, DOCX, TXT) |
| Create | `scripts/chapter_detector.py` | Heuristic chapter detection + fallback |
| Create | `scripts/writer.py` | Render extracted data to Markdown |
| Create | `scripts/tests/test_extractors.py` | Tests for extractor functions |
| Create | `scripts/tests/test_chapter_detector.py` | Tests for chapter detection logic |
| Create | `scripts/tests/test_writer.py` | Tests for Markdown writer |
| Create | `index/` | Output folder (gitignored contents optional) |
| Create | `requirements.txt` | `pymupdf` + `python-docx` |

---

## Task 1: Project scaffold and requirements

**Files:**
- Create: `requirements.txt`
- Create: `scripts/__init__.py`
- Create: `scripts/tests/__init__.py`
- Create: `index/.gitkeep`

- [ ] **Step 1: Create requirements.txt**

```
pymupdf
python-docx
pytest
```

- [ ] **Step 2: Create empty init files and index folder**

```bash
touch "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github/scripts/__init__.py"
touch "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github/scripts/tests/__init__.py"
mkdir -p "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github/index"
touch "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github/index/.gitkeep"
```

- [ ] **Step 3: Install dependencies**

```bash
pip install pymupdf python-docx pytest
```

Expected: all packages install without error.

- [ ] **Step 4: Commit scaffold**

```bash
git add requirements.txt scripts/ index/.gitkeep
git commit -m "feat: scaffold book indexer project"
```

---

## Task 2: Chapter detector

**Files:**
- Create: `scripts/chapter_detector.py`
- Create: `scripts/tests/test_chapter_detector.py`

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_chapter_detector.py`:

```python
from scripts.chapter_detector import detect_chapters, page_split

def test_detect_chapters_finds_titled_lines():
    pages = [
        "Chapter 1: The Beginning\n\nSome body text here that goes on for a while.",
        "Chapter 2: The Middle\n\nMore body text here.",
    ]
    chapters = detect_chapters(pages)
    assert len(chapters) == 2
    assert chapters[0]["title"] == "Chapter 1: The Beginning"
    assert "Some body text" in chapters[0]["text"]

def test_detect_chapters_fallback_to_page_split():
    pages = [f"Page {i} content with lots of text." for i in range(25)]
    chapters = detect_chapters(pages)
    # With no chapter headings, falls back to page_split groups
    assert len(chapters) > 0
    assert all("text" in c and "title" in c for c in chapters)

def test_page_split_groups_every_n_pages():
    pages = [f"page {i}" for i in range(30)]
    groups = page_split(pages, n=10)
    assert len(groups) == 3
    assert groups[0]["title"] == "Pages 1–10"
    assert groups[2]["title"] == "Pages 21–30"

def test_detect_chapters_empty_input():
    assert detect_chapters([]) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github"
python -m pytest scripts/tests/test_chapter_detector.py -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError`.

- [ ] **Step 3: Implement chapter_detector.py**

Create `scripts/chapter_detector.py`:

```python
import re
from typing import List, Dict

# Lines that look like chapter headings: short, title-case or uppercase,
# not ending with a period, optionally starting with "Chapter" or a number.
_HEADING_RE = re.compile(
    r'^(?:chapter\s+\d+[:\.\-]?\s+.{3,60}|part\s+\d+[:\.\-]?\s+.{3,60}|\d+[\.\)]\s+[A-Z].{3,50}|[A-Z][A-Z\s]{3,50})$',
    re.IGNORECASE
)


def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80 or line.endswith('.'):
        return False
    return bool(_HEADING_RE.match(line))


def detect_chapters(pages: List[str]) -> List[Dict]:
    """
    Try to detect chapters from a list of page strings.
    Returns list of dicts: [{"title": str, "text": str}, ...]
    Falls back to page_split if no headings found.
    """
    if not pages:
        return []

    chapters = []
    current_title = None
    current_lines = []

    for page in pages:
        for line in page.splitlines():
            if _is_heading(line):
                if current_title is not None:
                    chapters.append({
                        "title": current_title,
                        "text": "\n".join(current_lines).strip()
                    })
                current_title = line.strip()
                current_lines = []
            else:
                current_lines.append(line)

    # flush last chapter
    if current_title is not None:
        chapters.append({
            "title": current_title,
            "text": "\n".join(current_lines).strip()
        })

    # fallback: no chapters detected
    if not chapters:
        return page_split(pages, n=10)

    return chapters


def page_split(pages: List[str], n: int = 10) -> List[Dict]:
    """Group pages into chunks of n, returning titled dicts."""
    groups = []
    for i in range(0, len(pages), n):
        chunk = pages[i:i + n]
        start = i + 1
        end = i + len(chunk)
        groups.append({
            "title": f"Pages {start}–{end}",
            "text": "\n\n".join(chunk).strip()
        })
    return groups
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest scripts/tests/test_chapter_detector.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/chapter_detector.py scripts/tests/test_chapter_detector.py
git commit -m "feat: add chapter detector with page-split fallback"
```

---

## Task 3: Text extractors (PDF, DOCX, TXT)

**Files:**
- Create: `scripts/extractors.py`
- Create: `scripts/tests/test_extractors.py`

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_extractors.py`:

```python
import pathlib
import pytest
from scripts.extractors import extract_pdf, extract_docx, extract_txt, extract_file

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

def test_extract_txt_returns_pages():
    path = FIXTURES / "sample.txt"
    path.parent.mkdir(exist_ok=True)
    path.write_text("Hello world\nThis is a test.", encoding="utf-8")
    result = extract_txt(str(path))
    assert isinstance(result["pages"], list)
    assert len(result["pages"]) >= 1
    assert "Hello world" in result["pages"][0]
    assert result["title"] == "sample"
    assert result["source"] == "sample.txt"

def test_extract_file_dispatches_by_extension(tmp_path):
    txt = tmp_path / "book.txt"
    txt.write_text("Some content", encoding="utf-8")
    result = extract_file(str(txt))
    assert result["title"] == "book"

def test_extract_file_raises_on_unknown_extension(tmp_path):
    f = tmp_path / "book.xyz"
    f.write_text("data")
    with pytest.raises(ValueError, match="Unsupported"):
        extract_file(str(f))
```

- [ ] **Step 2: Create fixture file and run tests to verify they fail**

```bash
mkdir -p "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github/scripts/tests/fixtures"
python -m pytest scripts/tests/test_extractors.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement extractors.py**

Create `scripts/extractors.py`:

```python
import pathlib
from typing import Dict, List


def extract_pdf(path: str) -> Dict:
    """Extract pages from a PDF file. Returns dict with title, source, page_count, pages."""
    import fitz  # pymupdf

    doc = fitz.open(path)
    pages: List[str] = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    doc.close()

    stem = pathlib.Path(path).stem
    return {
        "title": stem,
        "source": pathlib.Path(path).name,
        "page_count": len(doc),
        "pages": pages,
    }


def extract_docx(path: str) -> Dict:
    """Extract paragraphs from a DOCX file as a single 'page'."""
    from docx import Document

    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    stem = pathlib.Path(path).stem
    # Group every 50 paragraphs as one "page"
    pages: List[str] = []
    for i in range(0, len(paragraphs), 50):
        pages.append("\n".join(paragraphs[i:i + 50]))

    return {
        "title": stem,
        "source": pathlib.Path(path).name,
        "page_count": len(pages),
        "pages": pages,
    }


def extract_txt(path: str) -> Dict:
    """Extract a TXT file. Treats the whole file as a list of 'pages' split by blank lines."""
    text = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    # Split on double newlines as pseudo-pages; fallback to whole file
    raw_pages = [p.strip() for p in text.split("\n\n") if p.strip()]
    pages = raw_pages if raw_pages else [text]
    stem = pathlib.Path(path).stem

    return {
        "title": stem,
        "source": pathlib.Path(path).name,
        "page_count": len(pages),
        "pages": pages,
    }


def extract_file(path: str) -> Dict:
    """Dispatch extraction by file extension."""
    ext = pathlib.Path(path).suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".docx":
        return extract_docx(path)
    elif ext == ".txt":
        return extract_txt(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest scripts/tests/test_extractors.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/extractors.py scripts/tests/test_extractors.py scripts/tests/fixtures/
git commit -m "feat: add PDF/DOCX/TXT extractors"
```

---

## Task 4: Markdown writer

**Files:**
- Create: `scripts/writer.py`
- Create: `scripts/tests/test_writer.py`

- [ ] **Step 1: Write failing tests**

Create `scripts/tests/test_writer.py`:

```python
from scripts.writer import render_markdown

def test_render_markdown_includes_title():
    data = {
        "title": "My Book",
        "source": "my-book.pdf",
        "page_count": 42,
        "chapters": [
            {"title": "Chapter 1", "text": "First chapter content."},
            {"title": "Chapter 2", "text": "Second chapter content."},
        ]
    }
    md = render_markdown(data)
    assert "# My Book" in md
    assert "**Source:** my-book.pdf" in md
    assert "**Pages:** 42" in md
    assert "## Table of Contents" in md
    assert "- Chapter 1" in md
    assert "- Chapter 2" in md
    assert "## Chapter 1" in md
    assert "First chapter content." in md

def test_render_markdown_handles_empty_chapters():
    data = {
        "title": "Empty Book",
        "source": "empty.txt",
        "page_count": 0,
        "chapters": []
    }
    md = render_markdown(data)
    assert "# Empty Book" in md
    assert "## Table of Contents" in md
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest scripts/tests/test_writer.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement writer.py**

Create `scripts/writer.py`:

```python
from datetime import date
from typing import Dict, List


def render_markdown(data: Dict) -> str:
    """
    Render a book dict to Markdown string.

    data keys: title, source, page_count, chapters
    chapters: list of {"title": str, "text": str}
    """
    today = date.today().isoformat()
    chapters: List[Dict] = data.get("chapters", [])

    lines = []

    # Header
    lines.append(f"# {data['title']}\n")
    lines.append(f"**Source:** {data['source']}  ")
    lines.append(f"**Pages:** {data['page_count']}  ")
    lines.append(f"**Extracted:** {today}\n")
    lines.append("---\n")

    # Table of contents
    lines.append("## Table of Contents\n")
    if chapters:
        for ch in chapters:
            lines.append(f"- {ch['title']}")
    else:
        lines.append("_(no chapters detected)_")
    lines.append("\n---\n")

    # Chapter sections
    for ch in chapters:
        lines.append(f"## {ch['title']}\n")
        lines.append(ch["text"])
        lines.append("\n---\n")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest scripts/tests/test_writer.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/writer.py scripts/tests/test_writer.py
git commit -m "feat: add markdown writer for book index files"
```

---

## Task 5: Main script (index_books.py)

**Files:**
- Create: `scripts/index_books.py`

- [ ] **Step 1: Implement index_books.py**

Create `scripts/index_books.py`:

```python
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

# Ensure scripts/ is on the path when run from repo root
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from scripts.extractors import extract_file
from scripts.chapter_detector import detect_chapters
from scripts.writer import render_markdown

REPO_ROOT = pathlib.Path(__file__).parent.parent
INDEX_DIR = REPO_ROOT / "index"
SUPPORTED = {".pdf", ".docx", ".txt"}


def sanitize_name(stem: str) -> str:
    """Convert filename stem to a safe markdown filename."""
    name = re.sub(r"[\s]+", "-", stem)
    name = re.sub(r"[^\w\-]", "", name)
    return name.strip("-")


def index_file(path: pathlib.Path, force: bool = False) -> None:
    out_name = sanitize_name(path.stem) + ".md"
    out_path = INDEX_DIR / out_name

    if out_path.exists() and not force:
        print(f"[SKIP] {path.name} — already indexed (use --force to re-index)")
        return

    try:
        data = extract_file(str(path))
        chapters = detect_chapters(data["pages"])
        data["chapters"] = chapters
        md = render_markdown(data)
        INDEX_DIR.mkdir(exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"[OK]   {path.name} → index/{out_name} ({data['page_count']} pages, {len(chapters)} sections)")
    except Exception as e:
        print(f"[FAIL] {path.name} — {e}")


def main():
    parser = argparse.ArgumentParser(description="Index books into Markdown files.")
    parser.add_argument("file", nargs="?", help="Single file to index (optional)")
    parser.add_argument("--force", action="store_true", help="Re-index even if output exists")
    args = parser.parse_args()

    if args.file:
        path = REPO_ROOT / args.file
        if not path.exists():
            print(f"[ERROR] File not found: {path}")
            sys.exit(1)
        index_file(path, force=args.force)
    else:
        files = [f for f in REPO_ROOT.iterdir() if f.suffix.lower() in SUPPORTED]
        if not files:
            print("No supported files found in repo root.")
            sys.exit(0)
        for f in sorted(files):
            index_file(f, force=args.force)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run against a single small file to verify it works**

```bash
cd "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github"
python scripts/index_books.py "48_Leyes_Poder_Todas_Leyes.txt"
```

Expected output:
```
[OK]   48_Leyes_Poder_Todas_Leyes.txt → index/48_Leyes_Poder_Todas_Leyes.md (N pages, N sections)
```

Then verify the file exists:
```bash
ls index/
```

- [ ] **Step 3: Run all tests to confirm nothing broke**

```bash
python -m pytest scripts/tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/index_books.py
git commit -m "feat: add main index_books.py script"
```

---

## Task 6: Index all books and verify output

- [ ] **Step 1: Run the full indexer**

```bash
cd "c:/Users/herna/OneDrive/Documents/Cursor Projectos/Libros-Github"
python scripts/index_books.py
```

Expected: one `[OK]` or `[SKIP]` line per book. No `[FAIL]` lines.

- [ ] **Step 2: Verify index files exist**

```bash
ls index/
```

Expected: one `.md` file per book in the repo root.

- [ ] **Step 3: Spot-check an index file**

```bash
head -40 "index/HABITOS-ATOMICOS-JAMES-CLEAR.md"
```

Expected: shows `# HABITOS-ATOMICOS-JAMES-CLEAR`, source, page count, table of contents with section names.

- [ ] **Step 4: Commit generated index files**

```bash
git add index/
git commit -m "feat: generate initial book index files"
```

---

## Task 7: Add .gitignore entry (optional — if user prefers not to commit generated files)

> Skip this task if the user wants index files committed to the repo (default).

- [ ] **Step 1: Add index/ to .gitignore**

```bash
echo "index/*.md" >> .gitignore
echo "!index/.gitkeep" >> .gitignore
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore generated index markdown files"
```
