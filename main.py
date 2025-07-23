import sys
import os
import logging
from src.extract_text import generate_bigfont_txts
from src.chapter_detector import extract_chapter_starts_from_txts
from src.pdf_saver import save_chapters
from src.config import FONT_SIZE_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "dom-casmurro.pdf"
    if not os.path.isfile(pdf_path):
        print(f"Arquivo não encontrado: {pdf_path}")
        sys.exit(1)

    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join("capitulos_extraidos", book_name)
    txt_dir = os.path.join("txt_fontes_grandes", book_name)

    font_size = FONT_SIZE_THRESHOLD
    chapter_starts = []

    while font_size >= 1:
        print(f"> Gerando .txt com fontes >= {font_size}...")
        generate_bigfont_txts(pdf_path, txt_dir, font_size)
        chapter_starts = extract_chapter_starts_from_txts(txt_dir)
        if chapter_starts:
            break
        logging.warning(f"Nenhum capítulo encontrado com font_size {font_size}, reduzindo...")
        font_size = 1  # força a última tentativa

    if not chapter_starts:
        logging.error("Nenhum capítulo detectado.")
        sys.exit(1)

    save_chapters(pdf_path, chapter_starts, output_dir)
    print("✅ Processamento finalizado!")

if __name__ == "__main__":
    main()
