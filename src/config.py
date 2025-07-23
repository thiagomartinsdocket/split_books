import re

FONT_SIZE_THRESHOLD = 16

CHAPTER_PATTERNS = [
    re.compile(r'(Capítulo|CAPÍTULO)'),
]

FALLBACK_PATTERNS = [
    re.compile(r'\b\d+\b'),
    re.compile(r'\b[IVXLCDM]+\b', re.IGNORECASE)
]
