from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

PDFS_DIR = PROJECT_ROOT / "pdfs"
DOWNLOADS_TEMP_DIR = PROJECT_ROOT / "downloads_temp"

SCRAPER_TIMEOUTS: dict[str, int] = {
    "RGE": 180,
    "DMAE": 300,
    "CORSAN": 300,
    "CEEE": 180,
}

CREDOR_SCRIPT: dict[str, Path] = {
    "RGE":    PROJECT_ROOT / "scripts" / "scraper_rge.py",
    "DMAE":   PROJECT_ROOT / "scripts" / "scraper_dmae.py",
    "CORSAN": PROJECT_ROOT / "scripts" / "scraper_corsan.py",
    "CEEE":   PROJECT_ROOT / "scripts" / "scraper_ceee.py",
}

CREDOR_PDF_DIR: dict[str, Path] = {
    "RGE":    PDFS_DIR / "RGE",
    "DMAE":   PDFS_DIR / "DMAE",
    "CORSAN": PDFS_DIR / "CORSAN",
    "CEEE":   PDFS_DIR / "CEEE",
}
