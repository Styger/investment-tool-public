import os
import shutil
from pathlib import Path


def cleanup_python_cache():
    """Lösche alle Python Cache Files"""
    project_root = Path(__file__).parent

    # Zähler
    pycache_count = 0
    pyc_count = 0

    # Finde und lösche __pycache__ Ordner
    for pycache in project_root.rglob("__pycache__"):
        print(f"Lösche: {pycache}")
        shutil.rmtree(pycache, ignore_errors=True)
        pycache_count += 1

    # Finde und lösche .pyc Files
    for pyc in project_root.rglob("*.pyc"):
        print(f"Lösche: {pyc}")
        pyc.unlink(missing_ok=True)
        pyc_count += 1

    print(f"\n✅ Cleanup abgeschlossen!")
    print(f"   {pycache_count} __pycache__ Ordner gelöscht")
    print(f"   {pyc_count} .pyc Files gelöscht")


if __name__ == "__main__":
    cleanup_python_cache()
