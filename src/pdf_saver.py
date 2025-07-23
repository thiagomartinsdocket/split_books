import os
import logging
from typing import List, Tuple
from pypdf import PdfReader, PdfWriter
from .utils import sanitize_filename

def save_chapters(pdf_path: str, chapter_starts: List[Tuple[int, str]], output_dir: str):
    reader = PdfReader(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    used_titles = set()

    for idx, (start, title) in enumerate(chapter_starts):
        end = chapter_starts[idx+1][0] if idx+1 < len(chapter_starts) else len(reader.pages)
        writer = PdfWriter()

        for i in range(start, end):
            writer.add_page(reader.pages[i])

        base = sanitize_filename(title.strip().replace(' ', '_'))
        chapter_name = f"{base}.pdf"
        if chapter_name in used_titles:
            chapter_name = f"{base}_{idx+1:02d}.pdf"
        used_titles.add(chapter_name)

        out_path = os.path.join(output_dir, chapter_name)
        with open(out_path, "wb") as f:
            writer.write(f)

        logging.info(f"Gerado: {out_path} (páginas {start+1}-{end})")
