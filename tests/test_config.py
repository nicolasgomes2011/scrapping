"""Testes de configuração do projeto."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CREDOR_PDF_DIR, CREDOR_SCRIPT, DOWNLOADS_TEMP_DIR, PDFS_DIR, PROJECT_ROOT, SCRAPER_TIMEOUTS

CREDORES = ["RGE", "DMAE", "CORSAN", "CEEE"]


def test_project_root_is_directory():
    assert PROJECT_ROOT.is_dir()


def test_scraper_timeouts_has_all_credores():
    for credor in CREDORES:
        assert credor in SCRAPER_TIMEOUTS, f"{credor} ausente em SCRAPER_TIMEOUTS"


def test_scraper_timeouts_values_are_positive_ints():
    for credor, timeout in SCRAPER_TIMEOUTS.items():
        assert isinstance(timeout, int), f"Timeout de {credor} não é int"
        assert timeout > 0, f"Timeout de {credor} deve ser positivo"


def test_credor_script_has_all_credores():
    for credor in CREDORES:
        assert credor in CREDOR_SCRIPT, f"{credor} ausente em CREDOR_SCRIPT"


def test_credor_script_files_exist():
    for credor, path in CREDOR_SCRIPT.items():
        assert path.exists(), f"Script de {credor} não encontrado: {path}"


def test_credor_pdf_dir_has_all_credores():
    for credor in CREDORES:
        assert credor in CREDOR_PDF_DIR, f"{credor} ausente em CREDOR_PDF_DIR"


def test_pdfs_dir_is_under_project_root():
    assert str(PDFS_DIR).startswith(str(PROJECT_ROOT))


def test_downloads_temp_dir_is_under_project_root():
    assert str(DOWNLOADS_TEMP_DIR).startswith(str(PROJECT_ROOT))
