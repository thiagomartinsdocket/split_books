import sys
import os
import re
import logging
from typing import List, Tuple
import pdfplumber
import pypdf


# Ajuste conforme necessário
FONT_SIZE_THRESHOLD = 16  # Tamanho mínimo da fonte para considerar como título
CHAPTER_PATTERNS = [
    re.compile(r'(Capítulo|CAPÍTULO)'),
]

FALLBACK_PATTERNS = [
    re.compile(r'\b\d+\b'),
    re.compile(r'\b[IVXLCDM]+\b', re.IGNORECASE)
]

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', name)

def generate_bigfont_txts(pdf_path: str, txt_dir: str, font_size: int) -> int:
    os.makedirs(txt_dir, exist_ok=True)
    page_count = 0
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            def filter_by_size(obj):
                return obj.get("size", 0) >= font_size
            filtered_page = page.filter(filter_by_size)
            text = filtered_page.extract_text() or ""
            with open(os.path.join(txt_dir, f"page_{i+1:03d}.txt"), "w", encoding="utf-8") as f:
                f.write(text)
            page_count += 1
    return page_count

def extract_chapter_starts_from_txts(txt_dir: str) -> List[Tuple[int, str]]:
    chapter_starts = []
    txt_files = sorted([f for f in os.listdir(txt_dir) if f.endswith('.txt')])
    # Primeira tentativa: padrão principal
    for idx, fname in enumerate(txt_files):
        with open(os.path.join(txt_dir, fname), encoding="utf-8") as f:
            text = f.read()
            for pattern in CHAPTER_PATTERNS:
                for match in pattern.finditer(text):
                    chapter_starts.append((idx, match.group(0)))
    # Se nada encontrado, tenta fallback
    if not chapter_starts:
        logging.warning("Nenhum capítulo detectado com o padrão principal. Tentando fallback com padrão decimal (\\d+)...")
        for idx, fname in enumerate(txt_files):
            with open(os.path.join(txt_dir, fname), encoding="utf-8") as f:
                text = f.read()
                for pattern in FALLBACK_PATTERNS:
                    for match in pattern.finditer(text):
                        chapter_starts.append((idx, match.group(0)))
        if chapter_starts:
            logging.info(f"Fallback detectou {len(chapter_starts)} possíveis capítulos usando padrão decimal.")
    return chapter_starts

def save_chapters(pdf_path: str, chapter_starts: List[Tuple[int, str]], output_dir: str):
    reader = pypdf.PdfReader(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    total = len(chapter_starts)
    used_titles = set()
    for idx, (start_page, title) in enumerate(chapter_starts):
        end_page = chapter_starts[idx+1][0] if idx+1 < total else len(reader.pages)
        writer = pypdf.PdfWriter()
        for p in range(start_page, end_page):
            writer.add_page(reader.pages[p])
        # Nome do arquivo pelo título do capítulo
        base_title = sanitize_filename(title.strip().replace(' ', '_'))
        chapter_name = f"{base_title}.pdf"
        # Evita sobrescrever arquivos com mesmo nome
        if chapter_name in used_titles:
            chapter_name = f"{base_title}_{idx+1:02d}.pdf"
        used_titles.add(chapter_name)
        out_path = os.path.join(output_dir, chapter_name)
        with open(out_path, 'wb') as f:
            writer.write(f)
        logging.info(f"Arquivo gerado: {out_path} (páginas {start_page+1}-{end_page})")

def main():
    if len(sys.argv) < 2:
        print("Uso: python extract_chapters_by_font.py <caminho_para_pdf>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Arquivo não encontrado: {pdf_path}")
        sys.exit(1)
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join('capitulos_extraidos', book_name)
    txt_dir = os.path.join('txt_fontes_grandes', book_name)

    font_size = FONT_SIZE_THRESHOLD
    min_font_size = 1
    chapter_starts = []
    while font_size >= min_font_size:
        print(f"Gerando arquivos .txt apenas com fontes >= {font_size} em {txt_dir}...")
        generate_bigfont_txts(pdf_path, txt_dir, font_size)
        chapter_starts = extract_chapter_starts_from_txts(txt_dir)
        if chapter_starts:
            break
        logging.warning(f"Nenhum capítulo detectado com FONT_SIZE_THRESHOLD={font_size}. Removendo validação por tamanho de fonte...")
        font_size -= 15
    if not chapter_starts:
        logging.error("Nenhum capítulo detectado mesmo após diminuir o FONT_SIZE_THRESHOLD.")
        sys.exit(1)
    logging.info(f"Capítulos detectados: {len(chapter_starts)}")
    for idx, (page_num, title) in enumerate(chapter_starts):
        logging.info(f"Capítulo {idx+1}: '{title}' na página {page_num+1}")
    save_chapters(pdf_path, chapter_starts, output_dir)
    print("Processamento finalizado!")

if __name__ == "__main__":
    main()
