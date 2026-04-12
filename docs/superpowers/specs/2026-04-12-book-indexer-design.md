# Book Indexer — Design Spec

**Date:** 2026-04-12  
**Status:** Approved

## Goal

Generate a Markdown index file per book inside a `/index` subfolder, so Claude Code can read any book's full structured text without processing the original PDF/DOCX/TXT files each session.

## Scope

- Input: all PDF, DOCX, and TXT files in the repo root
- Output: one `.md` per book in `/index/`
- Tool: a single Python script at `/scripts/index_books.py`
- Mode: offline, no external APIs

## Folder Structure

```
Libros-Github/
├── index/                              # Generated index files (one per book)
│   ├── HABITOS-ATOMICOS-JAMES-CLEAR.md
│   ├── la-psicologia-del-dinero-morgan-housel.md
│   ├── Tax-Free-Wealth.md
│   ├── El_poder_de_los_5_segundos.md
│   ├── Los-secretos-de-la-mente-millonaria.md
│   ├── 48-leyes-del-poder.md
│   └── Introduccion-IA.md
├── scripts/
│   └── index_books.py
└── *.pdf / *.docx / *.txt             # Original source files (untouched)
```

## Output Format (per `.md` file)

```markdown
# [Book Title]

**Source:** filename.pdf  
**Pages:** N  
**Extracted:** YYYY-MM-DD

---

## Table of Contents

- Chapter 1: ...
- Chapter 2: ...

---

## Chapter 1: Title

[Full extracted text...]

---

## Chapter 2: Title

[Full extracted text...]
```

Chapter detection: heuristic based on lines that are short, uppercase or title-case, and followed by body text. Falls back to page-based splits (every 10 pages = one section) if no chapters are detected.

## Script Behavior

- Scans repo root for `*.pdf`, `*.docx`, `*.txt`
- Skips files already indexed (unless `--force` flag passed)
- Sanitizes filenames for output (spaces → hyphens, special chars stripped)
- Prints progress per file: `[OK] HABITOS-ATOMICOS.md (247 pages)`
- On error: prints `[SKIP] filename.pdf — reason` and continues

## Dependencies

```
pymupdf       # PDF extraction
python-docx   # DOCX extraction
```

Install: `pip install pymupdf python-docx`

## Usage

```bash
# Index all books (skips already indexed)
python scripts/index_books.py

# Force re-index everything
python scripts/index_books.py --force

# Index a single file
python scripts/index_books.py "HABITOS-ATOMICOS-JAMES-CLEAR.pdf"
```

## Using the Index in Claude Code

```
Read index/HABITOS-ATOMICOS-JAMES-CLEAR.md
```

For very long books Claude Code will read in chunks using `offset` + `limit` parameters.

## Out of Scope

- Cross-book search
- API-based summarization
- Embeddings or vector search
- Auto-update on file change
