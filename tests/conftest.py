"""Fixtures compartilhadas entre todos os testes."""
import base64
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Garante que o projeto raiz esteja no sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import app as flask_app_module


@pytest.fixture()
def app():
    """Instância Flask configurada para testes."""
    flask_app_module.app.config["TESTING"] = True
    flask_app_module.app.config["PROPAGATE_EXCEPTIONS"] = False
    yield flask_app_module.app


@pytest.fixture()
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


@pytest.fixture()
def tmp_pdf_dir(tmp_path):
    """Diretório temporário com subpastas por credor."""
    for credor in ("DMAE", "CORSAN", "RGE", "CEEE"):
        (tmp_path / credor).mkdir()
    return tmp_path


@pytest.fixture()
def sample_pdf_bytes():
    """Bytes mínimos de um PDF válido."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"


@pytest.fixture()
def sample_pdf(tmp_path, sample_pdf_bytes):
    """Arquivo PDF temporário para testes."""
    pdf = tmp_path / "boleto.pdf"
    pdf.write_bytes(sample_pdf_bytes)
    return str(pdf)


@pytest.fixture()
def sample_pdf_base64(sample_pdf_bytes):
    """Base64 do PDF de exemplo."""
    return base64.b64encode(sample_pdf_bytes).decode("utf-8")


def make_subprocess_result(stdout: str = "", returncode: int = 0, stderr: str = ""):
    """Cria um mock de subprocess.CompletedProcess."""
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def rge_success_json(pdf_base64: str = "dGVzdA==") -> str:
    return json.dumps(
        {
            "arquivos": [
                {
                    "arquivo_original": "/tmp/rge.pdf",
                    "arquivo_salvo": "/tmp/rge_saved.pdf",
                    "sequencia": 1,
                    "tempo_download": "1.00s",
                    "pdf_base64": pdf_base64,
                }
            ],
            "metricas": {
                "tempo_total": "2.00s",
                "quantidade_faturas": 1,
                "tempo_medio_por_fatura": "2.00s",
            },
        }
    )


def ceee_success_json(pdf_base64: str = "dGVzdA==") -> str:
    return json.dumps(
        {
            "status": "sucesso",
            "arquivos": [
                {
                    "arquivo_salvo": "/tmp/ceee.pdf",
                    "pdf_base64": pdf_base64,
                }
            ],
        }
    )
