"""Gera o arquivo ZIP do projeto Moranguinho Stock Manager."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "Moranguinho-Stock-Manager.zip"
SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules"}
SKIP_EXT = {".db", ".pyc"}

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    return path.suffix.lower() in SKIP_EXT

def main():
    if OUT.exists():
        OUT.unlink()
    count = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in ROOT.rglob("*"):
            if f.is_file() and not should_skip(f.relative_to(ROOT)):
                arc = f.relative_to(ROOT.parent)
                zf.write(f, arc.as_posix())
                count += 1
    print(f"ZIP criado: {OUT}")
    print(f"Arquivos: {count}")
    print(f"Tamanho: {OUT.stat().st_size / 1024:.1f} KB")

if __name__ == "__main__":
    main()
