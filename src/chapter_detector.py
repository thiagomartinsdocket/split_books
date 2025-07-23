import os
import logging
from typing import List, Tuple
from .config import CHAPTER_PATTERNS, FALLBACK_PATTERNS

def extract_chapter_starts_from_txts(txt_dir: str) -> List[Tuple[int, str]]:
    chapter_starts = []
    txt_files = sorted([f for f in os.listdir(txt_dir) if f.endswith('.txt')])

    for idx, fname in enumerate(txt_files):
        with open(os.path.join(txt_dir, fname), encoding="utf-8") as f:
            text = f.read()
            for pattern in CHAPTER_PATTERNS:
                for match in pattern.finditer(text):
                    chapter_starts.append((idx, match.group(0)))

    if not chapter_starts:
        logging.warning("Nenhum capítulo detectado com padrão principal. Tentando fallback...")
        for idx, fname in enumerate(txt_files):
            with open(os.path.join(txt_dir, fname), encoding="utf-8") as f:
                text = f.read()
                for pattern in FALLBACK_PATTERNS:
                    for match in pattern.finditer(text):
                        chapter_starts.append((idx, match.group(0)))
        if chapter_starts:
            logging.info(f"Fallback detectou {len(chapter_starts)} possíveis capítulos.")
    
    return chapter_starts
