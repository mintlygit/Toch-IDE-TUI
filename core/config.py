import sys

#маппинг
LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".html": "html",
    ".css": "css", ".cpp": "cpp", ".rs": "rust", ".json": "json",
    ".md": "markdown"
}

RUN_COMMANDS = {
    ".py": f"{sys.executable}",
    ".js": "node",
    ".cpp": "g++ -o {stem} {path} && ./{stem}",
    ".rs": "rustc {path} -o {stem} && ./{stem}",
    ".sh": "bash",
}

KEYWORDS = {
    "python": ["print", "import", "from", "def", "class", "return", "if", "else", "elif", "for", "while", "try", "except", "with", "as", "async", "await", "None", "True", "False"],
    "javascript": ["console.log", "function", "const", "let", "var", "if", "else", "return", "import", "async", "await", "document", "window"],
    "cpp": ["#include", "int", "main", "std::cout", "std::endl", "if", "else", "return", "class", "public", "private"],
}
