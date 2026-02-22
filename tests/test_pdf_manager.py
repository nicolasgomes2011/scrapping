"""Testes unitários para utils/pdf_manager.py."""
import base64
import datetime
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.pdf_manager import PDFManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def manager(tmp_path):
    return PDFManager(base_dir=str(tmp_path))


@pytest.fixture()
def pdf_file(tmp_path):
    """Arquivo PDF mínimo para testes."""
    path = tmp_path / "test.pdf"
    path.write_bytes(b"%PDF-1.4\n%%EOF")
    return str(path)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

def test_init_creates_base_dir(tmp_path):
    base = tmp_path / "pdfs_test"
    PDFManager(base_dir=str(base))
    assert base.is_dir()


def test_init_default_dir_inside_project():
    m = PDFManager()
    assert "pdfs" in m.base_dir


# ---------------------------------------------------------------------------
# get_credor_dir
# ---------------------------------------------------------------------------

def test_get_credor_dir_creates_directory(manager, tmp_path):
    path = manager.get_credor_dir("dmae")
    assert os.path.isdir(path)
    assert path.endswith("DMAE")


def test_get_credor_dir_normalizes_name(manager):
    path1 = manager.get_credor_dir("rge")
    path2 = manager.get_credor_dir("RGE")
    assert path1 == path2


def test_get_credor_dir_strips_spaces(manager):
    path = manager.get_credor_dir("  CORSAN  ")
    assert os.path.basename(path) == "CORSAN"


# ---------------------------------------------------------------------------
# generate_filename
# ---------------------------------------------------------------------------

def test_generate_filename_basic(manager):
    name = manager.generate_filename("DMAE", "123456")
    assert name.startswith("DMAE_123456_")
    assert name.endswith(".pdf")


def test_generate_filename_with_date(manager):
    data = datetime.date(2024, 3, 15)
    name = manager.generate_filename("RGE", "999", data=data)
    assert "20240315" in name


def test_generate_filename_with_referencia(manager):
    name = manager.generate_filename("CORSAN", "555", referencia="03/2024")
    assert "REF_" in name
    assert "032024" in name


def test_generate_filename_sanitizes_instalacao(manager):
    name = manager.generate_filename("CEEE", "12-34/56")
    assert "123456" in name
    assert "-" not in name
    assert "/" not in name


def test_generate_filename_no_referencia_has_no_ref_token(manager):
    name = manager.generate_filename("DMAE", "001")
    assert "REF_" not in name


# ---------------------------------------------------------------------------
# save_pdf
# ---------------------------------------------------------------------------

def test_save_pdf_copies_to_credor_dir(manager, pdf_file, tmp_path):
    dest = manager.save_pdf(pdf_file, "DMAE", new_filename="boleto.pdf")
    assert os.path.exists(dest)
    assert "DMAE" in dest


def test_save_pdf_ensures_pdf_extension(manager, pdf_file):
    dest = manager.save_pdf(pdf_file, "RGE", new_filename="boleto")
    assert dest.endswith(".pdf")


def test_save_pdf_removes_crdownload_suffix(manager, tmp_path):
    crdownload = tmp_path / "boleto.pdf.crdownload"
    crdownload.write_bytes(b"%PDF-1.4\n%%EOF")
    dest = manager.save_pdf(str(crdownload), "CORSAN", new_filename="boleto.pdf.crdownload")
    assert dest.endswith(".pdf")
    assert ".crdownload" not in dest


def test_save_pdf_generates_name_from_instalacao(manager, pdf_file):
    dest = manager.save_pdf(pdf_file, "DMAE", numero_instalacao="777")
    assert "777" in os.path.basename(dest)


# ---------------------------------------------------------------------------
# file_to_base64
# ---------------------------------------------------------------------------

def test_file_to_base64_encodes_correctly(manager, tmp_path):
    content = b"hello pdf"
    f = tmp_path / "sample.pdf"
    f.write_bytes(content)
    result = manager.file_to_base64(str(f))
    assert result == base64.b64encode(content).decode("utf-8")


def test_file_to_base64_returns_empty_for_missing(manager):
    result = manager.file_to_base64("/nao/existe.pdf")
    assert result == ""


# ---------------------------------------------------------------------------
# get_pdf_metadata
# ---------------------------------------------------------------------------

def test_get_pdf_metadata_returns_dict(manager, pdf_file):
    meta = manager.get_pdf_metadata(pdf_file)
    assert meta is not None
    assert "tamanho_bytes" in meta
    assert "nome_arquivo" in meta
    assert "tamanho_formatado" in meta


def test_get_pdf_metadata_returns_none_for_missing(manager):
    result = manager.get_pdf_metadata("/nao/existe.pdf")
    assert result is None


def test_get_pdf_metadata_nome_arquivo(manager, pdf_file):
    meta = manager.get_pdf_metadata(pdf_file)
    assert meta["nome_arquivo"] == "test.pdf"


# ---------------------------------------------------------------------------
# _format_size
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bytes_val,expected", [
    (0, "0.00 B"),
    (512, "512.00 B"),
    (1024, "1.00 KB"),
    (1024 * 1024, "1.00 MB"),
    (1024 * 1024 * 1024, "1.00 GB"),
])
def test_format_size(bytes_val, expected):
    assert PDFManager._format_size(bytes_val) == expected


# ---------------------------------------------------------------------------
# listar_arquivos_recentes
# ---------------------------------------------------------------------------

def test_listar_arquivos_recentes_returns_recent(manager, tmp_path):
    recent = tmp_path / "recent.pdf"
    recent.write_bytes(b"data")
    result = manager.listar_arquivos_recentes(str(tmp_path), minutos=60)
    assert str(recent) in result


def test_listar_arquivos_recentes_ignores_subdirs(manager, tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    result = manager.listar_arquivos_recentes(str(tmp_path), minutos=60)
    assert not any(os.path.isdir(p) for p in result)


# ---------------------------------------------------------------------------
# limpar_arquivos_antigos
# ---------------------------------------------------------------------------

def test_limpar_arquivos_antigos_removes_old_files(manager, tmp_path):
    old_file = tmp_path / "old.pdf"
    old_file.write_bytes(b"data")
    # Forcefully set modification/access/creation time to far in the past
    old_timestamp = time.time() - (10 * 24 * 3600)  # 10 days ago
    os.utime(str(old_file), (old_timestamp, old_timestamp))
    removed = manager.limpar_arquivos_antigos(str(tmp_path), dias=7)
    assert removed >= 1
    assert not old_file.exists()


def test_limpar_arquivos_antigos_keeps_recent_files(manager, tmp_path):
    recent = tmp_path / "new.pdf"
    recent.write_bytes(b"data")
    removed = manager.limpar_arquivos_antigos(str(tmp_path), dias=7)
    assert removed == 0
    assert recent.exists()
