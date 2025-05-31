import libcst as cst
from typing import Iterable, Union
from pathlib import Path
import re
import pathspec
import logging

logger = logging.getLogger(__name__)


def extract_code_chunks(code, file_path):
    class CodeVisitor(cst.CSTVisitor):
        def __init__(self):
            self.chunks = []
            self.current_line = 1
        
        def visit_FunctionDef(self, node):
            chunk = node.code
            name = node.name.value
            start_line = node.get_metadata(cst.MetadataWrapper(node).position).start.line
            self.chunks.append({
                "text": chunk,
                "metadata": {
                    "type": "function",
                    "name": name,
                    "start_line": start_line,
                    "end_line": start_line + len(chunk.splitlines())
                }
            })
        
        def visit_ClassDef(self, node):
            chunk = node.code
            name = node.name.value
            start_line = node.get_metadata(cst.MetadataWrapper(node).position).start.line
            self.chunks.append({
                "text": chunk,
                "metadata": {
                    "type": "class",
                    "name": name,
                    "start_line": start_line,
                    "end_line": start_line + len(chunk.splitlines())
                }
            })
    
    try:
        tree = cst.parse_module(code)
        visitor = CodeVisitor()
        tree.visit(visitor)
        chunks = visitor.chunks
    except:
        chunks = []
    
    # Fallback for non-Python or unparsable files
    if not chunks:
        lines = code.splitlines()
        chunks = [{
            "text": code,
            "metadata": {
                "type": "file",
                "name": file_path.name,
                "start_line": 1,
                "end_line": len(lines)
            }
        }]
    
    return chunks

def load_gitignore_patterns(project_path: Path) -> pathspec.PathSpec:
    """Load .gitignore patterns from the project directory."""
    gitignore_path = project_path / ".gitignore"
    patterns = []
    
    if gitignore_path.exists():
        try:
            with gitignore_path.open("r") as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            logger.warning(f"Failed to read .gitignore: {e}")
    
    # Add default patterns as fallback
    default_patterns = [
        "venv/",
        "__pycache__/",
        "migrations/",
        ".git/",
        ".pytest_cache/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".env",
        "dist/",
        "build/"
    ]
    
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns + default_patterns)

def scan_project(path: Path, suffixes: Union[str, Iterable[str]] = (".py", ".html", ".md")):
    if isinstance(suffixes, str):
        suffixes = [suffixes]
    
    # Load .gitignore patterns
    gitignore_spec = load_gitignore_patterns(path)
    
    for suffix in suffixes:
        for file in path.rglob(f'*{suffix}'):
            if file.is_file():
                # Convert file path to relative for gitignore matching
                relative_path = file.relative_to(path).as_posix()
                if not gitignore_spec.match_file(relative_path):
                    yield file, extract_code_chunks(file.read_text(), file)