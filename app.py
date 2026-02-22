import base64
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from flask import Flask, jsonify, request
from pydantic import BaseModel, ValidationError

from config import CREDOR_PDF_DIR, CREDOR_SCRIPT, SCRAPER_TIMEOUTS

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["JSON_SORT_KEYS"] = False

# ---------------------------------------------------------------------------
# Environment — configurado uma vez na inicialização
# ---------------------------------------------------------------------------
_project_root = os.path.dirname(os.path.abspath(__file__))
_env = os.environ.copy()
_python_path = _env.get("PYTHONPATH", "")
_env["PYTHONPATH"] = f"{_project_root}{os.pathsep}{_python_path}"

# ---------------------------------------------------------------------------
# Pydantic schema de validação
# ---------------------------------------------------------------------------
class CredorRequest(BaseModel):
    id: int
    tipo_automacao: Literal["DMAE", "CORSAN", "RGE", "CEEE"]
    numero_instalacao: str
    cpf_cnpj: str
    usuario: str = ""
    senha: str = ""


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _run_subprocess(tipo: str, args: List[str]) -> subprocess.CompletedProcess:
    """Executa o script do credor via subprocess com o timeout configurado."""
    script = str(CREDOR_SCRIPT[tipo])
    timeout = SCRAPER_TIMEOUTS[tipo]
    cmd = [sys.executable, script] + args
    logger.info("Executando %s: %s", tipo, " ".join(cmd))
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_env,
        cwd=_project_root,
    )


def _extract_json_from_output(output: str) -> Optional[Dict]:
    """Extrai o último objeto JSON encontrado em uma string de saída."""
    matches = re.findall(r"\{.*\}", output, re.DOTALL)
    if not matches:
        return None
    for candidate in reversed(matches):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _find_latest_pdf(tipo: str, numero_instalacao: str) -> Optional[str]:
    """Retorna o caminho do PDF mais recente para a instalação no diretório do credor."""
    pdf_dir = str(CREDOR_PDF_DIR[tipo])
    os.makedirs(pdf_dir, exist_ok=True)
    all_files = os.listdir(pdf_dir)
    matches = sorted(
        [f for f in all_files if f.endswith(".pdf") and numero_instalacao in f],
        reverse=True,
    )
    if matches:
        return os.path.join(pdf_dir, matches[0])
    return None


def _file_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _erro(mensagem: str) -> Dict[str, Any]:
    return {"status": "erro", "documentos": [], "metricas": {}, "erro": mensagem}


def _sucesso(documentos: List[Dict], metricas: Optional[Dict] = None) -> Dict[str, Any]:
    return {
        "status": "sucesso",
        "documentos": documentos,
        "metricas": metricas or {},
        "erro": None,
    }


# ---------------------------------------------------------------------------
# Executores por tipo
# ---------------------------------------------------------------------------

def executar_script_rge(credor: CredorRequest) -> Dict[str, Any]:
    try:
        result = _run_subprocess(
            "RGE",
            [credor.numero_instalacao, credor.cpf_cnpj, credor.usuario, credor.senha],
        )

        if result.returncode != 0:
            logger.error("RGE returncode=%d stderr=%s", result.returncode, result.stderr[:300])
            return _erro(result.stderr or "Erro ao executar script RGE")

        dados = _extract_json_from_output(result.stdout.strip())
        if not dados or "arquivos" not in dados:
            return _erro("Formato inesperado na saída do script RGE")

        documentos = []
        for arq in dados["arquivos"]:
            doc: Dict[str, Any] = {
                "arquivo_baixado": arq.get("arquivo_salvo", ""),
                "sequencia": arq.get("sequencia", 1),
            }
            if arq.get("pdf_base64"):
                doc["pdf_base64"] = arq["pdf_base64"]
            documentos.append(doc)

        return _sucesso(documentos, dados.get("metricas"))

    except subprocess.TimeoutExpired:
        return _erro("Timeout ao executar script RGE")
    except Exception as exc:
        logger.exception("Exceção inesperada ao executar RGE")
        return _erro(str(exc))


def executar_script_dmae(credor: CredorRequest) -> Dict[str, Any]:
    try:
        _run_subprocess("DMAE", [credor.numero_instalacao, credor.cpf_cnpj])
    except subprocess.TimeoutExpired:
        logger.warning("DMAE timeout — tentando recuperar PDF do disco")
    except Exception as exc:
        logger.warning("DMAE subprocess falhou: %s — tentando recuperar PDF do disco", exc)

    pdf_path = _find_latest_pdf("DMAE", credor.numero_instalacao)
    if not pdf_path:
        return _erro(f"Nenhum PDF encontrado para instalação {credor.numero_instalacao}")

    logger.info("DMAE PDF encontrado: %s", pdf_path)
    return _sucesso([{"arquivo_baixado": pdf_path, "sequencia": 1, "pdf_base64": _file_to_base64(pdf_path)}])


def executar_script_corsan(credor: CredorRequest) -> Dict[str, Any]:
    try:
        _run_subprocess("CORSAN", [credor.cpf_cnpj, credor.numero_instalacao])
    except subprocess.TimeoutExpired:
        logger.warning("CORSAN timeout — tentando recuperar PDF do disco")
    except Exception as exc:
        logger.warning("CORSAN subprocess falhou: %s — tentando recuperar PDF do disco", exc)

    pdf_path = _find_latest_pdf("CORSAN", credor.numero_instalacao)
    if not pdf_path:
        return _erro(f"Nenhum PDF encontrado para instalação {credor.numero_instalacao}")

    logger.info("CORSAN PDF encontrado: %s", pdf_path)
    return _sucesso([{"arquivo_baixado": pdf_path, "sequencia": 1, "pdf_base64": _file_to_base64(pdf_path)}])


def executar_script_ceee(credor: CredorRequest) -> Dict[str, Any]:
    try:
        result = _run_subprocess("CEEE", [credor.numero_instalacao, credor.cpf_cnpj])

        if result.returncode != 0:
            return _erro(result.stderr or "Erro ao executar script CEEE")

        output = result.stdout.strip()
        if not output:
            return _sucesso([{"arquivo_baixado": "CEEE executado com sucesso"}])

        dados = _extract_json_from_output(output)
        if dados and "arquivos" in dados:
            documentos = []
            for arq in dados["arquivos"]:
                doc: Dict[str, Any] = {"arquivo_baixado": arq.get("arquivo_salvo", "")}
                if arq.get("pdf_base64"):
                    doc["pdf_base64"] = arq["pdf_base64"]
                documentos.append(doc)
            return _sucesso(documentos)

        return _sucesso([{"arquivo_baixado": "CEEE executado com sucesso"}])

    except subprocess.TimeoutExpired:
        return _erro("Timeout ao executar script CEEE")
    except Exception as exc:
        logger.exception("Exceção inesperada ao executar CEEE")
        return _erro(str(exc))


_EXECUTORES = {
    "RGE": executar_script_rge,
    "DMAE": executar_script_dmae,
    "CORSAN": executar_script_corsan,
    "CEEE": executar_script_ceee,
}

# ---------------------------------------------------------------------------
# Rota principal
# ---------------------------------------------------------------------------

@app.route("/api/processar-credores", methods=["POST"])
def processar_credores():
    inicio = datetime.now()
    logger.info("Iniciando processamento de credores em %s", inicio.isoformat())

    body = request.get_json(silent=True)
    if not body or "credores" not in body:
        return jsonify({"erro": "Formato inválido. Forneça {'credores': [...]}"}), 400

    resultados = []
    for item in body["credores"]:
        try:
            credor = CredorRequest(**item)
        except ValidationError as exc:
            resultado: Dict[str, Any] = {
                "id_credor": item.get("id"),
                "tipo_automacao": item.get("tipo_automacao"),
                "numero_instalacao": item.get("numero_instalacao"),
                **_erro(f"Dados inválidos: {exc.errors()}"),
            }
            resultados.append(resultado)
            continue

        logger.info("Processando credor id=%s tipo=%s", credor.id, credor.tipo_automacao)
        executor = _EXECUTORES[credor.tipo_automacao]
        resultado = executor(credor)
        resultado.update(
            {
                "id_credor": credor.id,
                "numero_instalacao": credor.numero_instalacao,
                "tipo_automacao": credor.tipo_automacao,
            }
        )
        resultados.append(resultado)

    return jsonify(
        {
            "resultados": resultados,
            "total_credores": len(body["credores"]),
            "processado_em": inicio.isoformat(),
        }
    )


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, threaded=True, debug=False)
