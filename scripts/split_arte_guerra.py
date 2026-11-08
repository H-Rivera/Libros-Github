#!/usr/bin/env python3
"""
split_arte_guerra.py — Divide 'The Art of War' (Sun Tzu, trad. Lionel Giles,
Project Gutenberg #132) en un .md por capitulo dentro de
index/el-arte-de-la-guerra/

Usage:
    python scripts/split_arte_guerra.py
"""

import pathlib
import re
from datetime import date

REPO_ROOT = pathlib.Path(__file__).parent.parent
TXT_PATH = REPO_ROOT / "The-Art-of-War-Sun-Tzu.txt"
OUT_DIR = REPO_ROOT / "index" / "el-arte-de-la-guerra"

CHAPTER_RE = re.compile(r'^Chapter ([IVXLC]+)\. (.+)$')
END_RE = re.compile(r'^\*\*\* END OF THE PROJECT GUTENBERG EBOOK')

# Titulos en espanol (traduccion habitual) para el indice
TITULOS_ES = {
    1: "Planificación",
    2: "La conducción de la guerra",
    3: "El ataque por estratagema",
    4: "Disposiciones tácticas",
    5: "La energía",
    6: "Puntos débiles y fuertes",
    7: "Maniobras",
    8: "Variación de tácticas",
    9: "El ejército en marcha",
    10: "El terreno",
    11: "Las nueve situaciones",
    12: "El ataque con fuego",
    13: "El uso de espías",
}


def find_chapters(lines):
    """Returns list of (num, title_en, start_line, end_line)."""
    starts = []
    end_of_book = len(lines)
    for i, line in enumerate(lines):
        # Sin strip(): las entradas indentadas de la tabla de contenido no cuentan
        m = CHAPTER_RE.match(line.rstrip())
        if m:
            starts.append((len(starts) + 1, m.group(2).strip(), i))
        elif END_RE.match(line):
            end_of_book = i
            break
    chapters = []
    for idx, (num, title, start) in enumerate(starts):
        end = starts[idx + 1][2] if idx + 1 < len(starts) else end_of_book
        chapters.append((num, title, start, end))
    return chapters


def render_chapter_md(num, title_en, body_lines):
    today = date.today().isoformat()
    title_es = TITULOS_ES.get(num, "")
    body = "\n".join(body_lines).strip()
    body = re.sub(r'\n{3,}', '\n\n', body)
    out = [
        f"# Capítulo {num}: {title_es} ({title_en.title()})\n",
        "**Libro:** El arte de la guerra — Sun Tzu (trad. al inglés de Lionel Giles, 1910)  ",
        "**Fuente:** Project Gutenberg #132 (dominio público)  ",
        f"**Extraido:** {today}\n",
        "---\n",
        body,
        "",
    ]
    return "\n".join(out)


def main():
    lines = TXT_PATH.read_text(encoding="utf-8").splitlines()
    chapters = find_chapters(lines)
    print(f"  {len(chapters)} capitulos detectados")
    if len(chapters) != 13:
        print("[ERROR] Se esperaban 13 capitulos. Revisa el archivo.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "# El arte de la guerra — Indice\n",
        "**Autor:** Sun Tzu  ",
        "**Traduccion:** Lionel Giles (1910), en inglés — Project Gutenberg #132, dominio público\n",
        "---\n",
    ]
    for num, title_en, start, end in chapters:
        filename = f"capitulo-{num:02d}.md"
        md = render_chapter_md(num, title_en, lines[start + 1:end])
        (OUT_DIR / filename).write_text(md, encoding="utf-8")
        index_lines.append(f"- [{num}. {TITULOS_ES[num]} — {title_en.title()}]({filename})")
        size_kb = (OUT_DIR / filename).stat().st_size / 1024
        print(f"[OK]   {filename} — {title_en} ({size_kb:.1f} KB)")

    (OUT_DIR / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"[OK]   README.md -> indice de {len(chapters)} capitulos")


if __name__ == "__main__":
    main()
