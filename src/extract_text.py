import os
import pdfplumber

def generate_bigfont_txts(pdf_path: str, txt_dir: str, font_size: int) -> int:
    os.makedirs(txt_dir, exist_ok=True)
    page_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            filtered = page.filter(lambda obj: obj.get("size", 0) >= font_size)
            text = filtered.extract_text() or ""
            with open(os.path.join(txt_dir, f"page_{i+1:03d}.txt"), "w", encoding="utf-8") as f:
                f.write(text)
            page_count += 1

    return page_count
