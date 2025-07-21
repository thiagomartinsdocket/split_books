DEBUG_MODE = True  # Ative para salvar logs detalhados de detecção
MIN_WORDS = 100  # mínimo de palavras para considerar um capítulo válido
MIN_CHARS = 500  # mínimo de caracteres para considerar um capítulo válido

def is_valid_chapter(text: str) -> bool:
    """Valida se o texto do capítulo tem tamanho suficiente."""
    words = len(text.split())
    chars = len(text)
    return words >= MIN_WORDS and chars >= MIN_CHARS
import sys
import os
import re
import logging
from typing import List, Tuple
from pypdf import PdfReader, PdfWriter # type: ignore


def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos."""
    return re.sub(r'[^\w\-_\. ]', '_', name)

def save_chapters(reader: PdfReader, chapter_starts: List[Tuple[int, str]], pdf_path: str, output_dir: str) -> List[int]:
    """
    Salva cada capítulo detectado como um novo arquivo PDF.
    Retorna lista de páginas problemáticas (mais de um capítulo na mesma página).
    """
    os.makedirs(output_dir, exist_ok=True)
    problem_pages = []
    total = len(chapter_starts)
    processed_titles = set()
    for idx, (start_page, title) in enumerate(chapter_starts):
        # Normaliza o título para evitar processar capítulos repetidos
        norm_title = title.strip().lower()
        if norm_title in processed_titles:
            logging.warning(f"Capítulo repetido ignorado: '{title}' na página {start_page+1}")
            continue
        processed_titles.add(norm_title)
        end_page = chapter_starts[idx+1][0] if idx+1 < total else len(reader.pages)
        # Extrai texto do capítulo para validação
        chapter_text = ""
        for p in range(start_page, end_page):
            chapter_text += reader.pages[p].extract_text() or ""
        if not is_valid_chapter(chapter_text):
            logging.warning(f"Capítulo ignorado por ser muito curto: '{title}' na página {start_page+1} (palavras: {len(chapter_text.split())}, caracteres: {len(chapter_text)})")
            continue
        writer = PdfWriter()
        # Se dois capítulos começam na mesma página, marcar como problemático
        if idx+1 < total and start_page == chapter_starts[idx+1][0]:
            problem_pages.append(start_page+1)
        for p in range(start_page, end_page):
            writer.add_page(reader.pages[p])
        chapter_name = sanitize_filename(f"{idx+1:02d}_{title.strip().replace(' ', '_')}.pdf")
        out_path = os.path.join(output_dir, chapter_name)
        with open(out_path, 'wb') as f:
            writer.write(f)
        logging.info(f"Arquivo gerado: {out_path} (páginas {start_page+1}-{end_page}) | Palavras: {len(chapter_text.split())} | Caracteres: {len(chapter_text)}")
    return problem_pages

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Expressões regulares para identificar títulos de capítulos
CHAPTER_PATTERNS = [
    re.compile(r"cap[ií]tulo\s+\d+", re.IGNORECASE),
    re.compile(r"cap\.\s*\d+", re.IGNORECASE),
    re.compile(r"chapter\s+\d+", re.IGNORECASE),
    # Adicione outros padrões conforme necessário
]

def extract_chapter_starts(reader: PdfReader) -> List[Tuple[int, str]]:
    """
    Retorna uma lista de tuplas (número da página, título do capítulo encontrado)
    """
    chapter_starts = []
    IGNORE_CONTEXT = [
        "anterior", "anteriores", "vimos no", "veja", "como vimos", "conforme", "sobre", "leia", "consulte",
        "mencionado", "mencionados", "mencionadas", "citados", "citadas", "citando", "referência", "referido",
        "referida", "referidos", "referidas", "próximo", "próximos", "seguinte", "seguintes", "nos ", "no "
    ]
    debug_lines = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        lines = text.splitlines()
        for line_num, line in enumerate(lines):
            for pattern in CHAPTER_PATTERNS:
                for match in pattern.finditer(line):
                    context = line[max(0, match.start()-60):match.start()].lower()
                    if any(word in context for word in IGNORE_CONTEXT):
                        continue
                    if len(re.findall(r"cap[ií]tulo|cap\. |chapter", line, re.IGNORECASE)) > 1:
                        continue
                    chapter_starts.append((i, match.group(0)))
                    if DEBUG_MODE:
                        debug_lines.append(f"[P{str(i+1).zfill(3)}][L{str(line_num+1).zfill(3)}] {line.strip()}")
        if DEBUG_MODE:
            with open(f"debug_paginas.txt", "a", encoding="utf-8") as dbg:
                dbg.write(f"\n--- Página {i+1} ---\n{text}\n")
    if DEBUG_MODE and debug_lines:
        with open("debug_capitulos_detectados.txt", "w", encoding="utf-8") as dbg:
            dbg.write("\n".join(debug_lines))
    return chapter_starts

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <caminho_para_pdf>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Arquivo não encontrado: {pdf_path}")
        sys.exit(1)
    reader = PdfReader(pdf_path)
    logging.info(f"PDF carregado: {pdf_path} ({len(reader.pages)} páginas)")
    chapter_starts = extract_chapter_starts(reader)
    logging.info(f"Capítulos detectados: {len(chapter_starts)}")
    for idx, (page_num, title) in enumerate(chapter_starts):
        logging.info(f"Capítulo {idx+1}: '{title}' na página {page_num+1}")

    # Pasta de saída organizada pelo nome do livro
    book_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join('capitulos_extraidos', book_name)
    problem_pages = save_chapters(reader, chapter_starts, pdf_path, output_dir)

    # Relatório simples
    print("\nResumo do processamento:")
    print(f"Capítulos detectados: {len(chapter_starts)}")
    print(f"Arquivos gerados: {len(chapter_starts)}")
    if problem_pages:
        print(f"Páginas problemáticas (mais de um capítulo na mesma página): {problem_pages}")
    else:
        print("Nenhuma página problemática detectada.")

if __name__ == "__main__":
    main()
