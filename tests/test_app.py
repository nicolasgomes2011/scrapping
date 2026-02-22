"""Testes de integração para as rotas Flask de app.py."""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.conftest import ceee_success_json, make_subprocess_result, rge_success_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def post_credores(client, credores):
    return client.post(
        "/api/processar-credores",
        json={"credores": credores},
        content_type="application/json",
    )


def credor_rge(**kwargs):
    base = {
        "id": 1,
        "tipo_automacao": "RGE",
        "numero_instalacao": "123456",
        "cpf_cnpj": "12345678901",
        "usuario": "user",
        "senha": "pass",
    }
    base.update(kwargs)
    return base


def credor_dmae(**kwargs):
    base = {
        "id": 2,
        "tipo_automacao": "DMAE",
        "numero_instalacao": "654321",
        "cpf_cnpj": "98765432100",
    }
    base.update(kwargs)
    return base


def credor_corsan(**kwargs):
    base = {
        "id": 3,
        "tipo_automacao": "CORSAN",
        "numero_instalacao": "111222",
        "cpf_cnpj": "11122233344",
    }
    base.update(kwargs)
    return base


def credor_ceee(**kwargs):
    base = {
        "id": 4,
        "tipo_automacao": "CEEE",
        "numero_instalacao": "000935034",
        "cpf_cnpj": "06210667000103",
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Testes de validação de entrada
# ---------------------------------------------------------------------------

def test_post_sem_body_retorna_400(client):
    resp = client.post("/api/processar-credores", data="not json", content_type="application/json")
    assert resp.status_code == 400


def test_post_sem_chave_credores_retorna_400(client):
    resp = client.post("/api/processar-credores", json={"outro": []})
    assert resp.status_code == 400


def test_tipo_automacao_invalido_retorna_erro_no_resultado(client):
    resp = post_credores(client, [{"id": 1, "tipo_automacao": "INVALIDO", "numero_instalacao": "x", "cpf_cnpj": "x"}])
    assert resp.status_code == 200
    data = resp.get_json()
    resultado = data["resultados"][0]
    assert resultado["status"] == "erro"


def test_campos_obrigatorios_faltando_retorna_erro_no_resultado(client):
    # Falta numero_instalacao e cpf_cnpj
    resp = post_credores(client, [{"id": 1, "tipo_automacao": "RGE"}])
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"


# ---------------------------------------------------------------------------
# Resposta padrão
# ---------------------------------------------------------------------------

def test_resposta_contem_campos_obrigatorios(client, tmp_path):
    num = "123456"
    pdf = tmp_path / f"RGE_{num}_20240101.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")
    fake_result = make_subprocess_result(stdout=rge_success_json())
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_rge(numero_instalacao=num)])
    data = resp.get_json()
    assert "resultados" in data
    assert "total_credores" in data
    assert "processado_em" in data


def test_total_credores_corresponde_ao_input(client):
    fake_result = make_subprocess_result(stdout=rge_success_json())
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_rge(), credor_rge(id=2)])
    data = resp.get_json()
    assert data["total_credores"] == 2
    assert len(data["resultados"]) == 2


# ---------------------------------------------------------------------------
# RGE
# ---------------------------------------------------------------------------

def test_rge_sucesso_com_base64(client):
    fake_stdout = rge_success_json(pdf_base64="dGVzdA==")
    fake_result = make_subprocess_result(stdout=fake_stdout)
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_rge()])
    data = resp.get_json()
    resultado = data["resultados"][0]
    assert resultado["status"] == "sucesso"
    assert len(resultado["documentos"]) == 1
    assert resultado["documentos"][0]["pdf_base64"] == "dGVzdA=="


def test_rge_subprocess_erro_retorna_status_erro(client):
    fake_result = make_subprocess_result(returncode=1, stderr="Falha de login")
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_rge()])
    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"
    assert "Falha de login" in data["resultados"][0]["erro"]


def test_rge_timeout_retorna_status_erro(client):
    with patch("app._run_subprocess", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1)):
        resp = post_credores(client, [credor_rge()])
    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"
    assert "Timeout" in data["resultados"][0]["erro"]


def test_rge_saida_json_invalida_retorna_erro(client):
    fake_result = make_subprocess_result(stdout="isso nao e json", returncode=0)
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_rge()])
    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"


# ---------------------------------------------------------------------------
# DMAE
# ---------------------------------------------------------------------------

def test_dmae_sucesso_encontra_pdf_no_disco(client, tmp_path):
    num = "654321"
    pdf = tmp_path / f"DMAE_{num}_20240101.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    fake_result = make_subprocess_result(stdout="")
    with (
        patch("app._run_subprocess", return_value=fake_result),
        patch("app.CREDOR_PDF_DIR", {"DMAE": tmp_path, "CORSAN": tmp_path, "RGE": tmp_path, "CEEE": tmp_path}),
    ):
        resp = post_credores(client, [credor_dmae(numero_instalacao=num)])

    data = resp.get_json()
    resultado = data["resultados"][0]
    assert resultado["status"] == "sucesso"
    assert resultado["documentos"][0]["pdf_base64"] != ""


def test_dmae_sem_pdf_no_disco_retorna_erro(client, tmp_path):
    fake_result = make_subprocess_result(stdout="")
    with (
        patch("app._run_subprocess", return_value=fake_result),
        patch("app.CREDOR_PDF_DIR", {"DMAE": tmp_path, "CORSAN": tmp_path, "RGE": tmp_path, "CEEE": tmp_path}),
    ):
        resp = post_credores(client, [credor_dmae(numero_instalacao="999999")])

    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"


def test_dmae_timeout_still_tries_disk(client, tmp_path):
    num = "654321"
    pdf = tmp_path / f"DMAE_{num}_20240101.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    with (
        patch("app._run_subprocess", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1)),
        patch("app.CREDOR_PDF_DIR", {"DMAE": tmp_path, "CORSAN": tmp_path, "RGE": tmp_path, "CEEE": tmp_path}),
    ):
        resp = post_credores(client, [credor_dmae(numero_instalacao=num)])

    data = resp.get_json()
    # Mesmo com timeout, se o PDF está no disco deve retornar sucesso
    assert data["resultados"][0]["status"] == "sucesso"


# ---------------------------------------------------------------------------
# CORSAN
# ---------------------------------------------------------------------------

def test_corsan_sucesso_encontra_pdf_no_disco(client, tmp_path):
    num = "111222"
    pdf = tmp_path / f"CORSAN_{num}_20240101.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF")

    fake_result = make_subprocess_result(stdout="")
    with (
        patch("app._run_subprocess", return_value=fake_result),
        patch("app.CREDOR_PDF_DIR", {"DMAE": tmp_path, "CORSAN": tmp_path, "RGE": tmp_path, "CEEE": tmp_path}),
    ):
        resp = post_credores(client, [credor_corsan(numero_instalacao=num)])

    data = resp.get_json()
    assert data["resultados"][0]["status"] == "sucesso"


def test_corsan_sem_pdf_no_disco_retorna_erro(client, tmp_path):
    fake_result = make_subprocess_result(stdout="")
    with (
        patch("app._run_subprocess", return_value=fake_result),
        patch("app.CREDOR_PDF_DIR", {"DMAE": tmp_path, "CORSAN": tmp_path, "RGE": tmp_path, "CEEE": tmp_path}),
    ):
        resp = post_credores(client, [credor_corsan(numero_instalacao="000000")])

    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"


# ---------------------------------------------------------------------------
# CEEE
# ---------------------------------------------------------------------------

def test_ceee_sucesso_com_base64(client):
    fake_result = make_subprocess_result(stdout=ceee_success_json(pdf_base64="dGVzdA=="))
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_ceee()])
    data = resp.get_json()
    resultado = data["resultados"][0]
    assert resultado["status"] == "sucesso"


def test_ceee_subprocess_erro_retorna_status_erro(client):
    fake_result = make_subprocess_result(returncode=1, stderr="CEEE falhou")
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_ceee()])
    data = resp.get_json()
    assert data["resultados"][0]["status"] == "erro"


# ---------------------------------------------------------------------------
# Múltiplos credores
# ---------------------------------------------------------------------------

def test_multiplos_credores_processados(client, tmp_path):
    num_dmae = "654321"
    num_corsan = "111222"
    pdf_dmae = tmp_path / f"DMAE_{num_dmae}_20240101.pdf"
    pdf_corsan = tmp_path / f"CORSAN_{num_corsan}_20240101.pdf"
    pdf_dmae.write_bytes(b"%PDF-1.4\n%%EOF")
    pdf_corsan.write_bytes(b"%PDF-1.4\n%%EOF")

    fake_stdout_rge = rge_success_json()
    fake_result = make_subprocess_result(stdout=fake_stdout_rge)

    with (
        patch("app._run_subprocess", return_value=fake_result),
        patch("app.CREDOR_PDF_DIR", {"DMAE": tmp_path, "CORSAN": tmp_path, "RGE": tmp_path, "CEEE": tmp_path}),
    ):
        resp = post_credores(
            client,
            [
                credor_rge(id=1),
                credor_dmae(id=2, numero_instalacao=num_dmae),
                credor_corsan(id=3, numero_instalacao=num_corsan),
            ],
        )

    data = resp.get_json()
    assert data["total_credores"] == 3
    assert len(data["resultados"]) == 3


def test_resultados_contem_id_credor_e_tipo(client):
    fake_result = make_subprocess_result(stdout=rge_success_json())
    with patch("app._run_subprocess", return_value=fake_result):
        resp = post_credores(client, [credor_rge(id=42)])
    resultado = resp.get_json()["resultados"][0]
    assert resultado["id_credor"] == 42
    assert resultado["tipo_automacao"] == "RGE"
    assert resultado["numero_instalacao"] == "123456"
