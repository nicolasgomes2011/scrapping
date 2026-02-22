#!/usr/bin/env python3
"""
Módulo para gerenciar arquivos PDF de contas de serviços públicos.
Oferece uma solução centralizada para salvar, renomear, organizar PDFs
por credores e realizar operações de manutenção de arquivos.
"""
import base64
import datetime
import logging
import os
import shutil
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFManager:
    """
    Gerenciador de arquivos PDF para contas de serviços públicos.

    Fornece métodos para:
    - Criar a estrutura de diretórios necessária para organizar PDFs por credor
    - Salvar PDFs em uma estrutura padronizada
    - Gerar nomes de arquivos padronizados por credor
    - Listar e remover arquivos antigos de diretórios de download
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """
        Inicializa o gerenciador de PDFs.

        Args:
            base_dir: Diretório base para salvar os PDFs.
                      Se None, usa 'pdfs' no diretório raiz do projeto.
        """
        if base_dir is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            self.base_dir = os.path.join(project_root, "pdfs")
        else:
            self.base_dir = base_dir

        os.makedirs(self.base_dir, exist_ok=True)
        logger.info("PDFManager iniciado com diretório base: %s", self.base_dir)

    def get_credor_dir(self, credor_nome: str) -> str:
        """
        Retorna o caminho do diretório para um credor, criando-o se necessário.

        Args:
            credor_nome: Nome do credor (ex: "DMAE", "RGE", "CEEE", "CORSAN").

        Returns:
            Caminho completo para o diretório do credor.
        """
        credor_nome = credor_nome.strip().upper()
        credor_dir = os.path.join(self.base_dir, credor_nome)
        os.makedirs(credor_dir, exist_ok=True)
        return credor_dir

    def generate_filename(
        self,
        credor_nome: str,
        numero_instalacao: str,
        data: Optional[datetime.date] = None,
        referencia: Optional[str] = None,
    ) -> str:
        """
        Gera um nome de arquivo padronizado para a conta.

        Args:
            credor_nome: Nome do credor (ex: "DMAE").
            numero_instalacao: Número da instalação/matrícula.
            data: Data da conta. Se None, usa a data atual.
            referencia: Mês/ano de referência (ex: "09/2023").

        Returns:
            Nome do arquivo no formato CREDOR_INSTALACAO_YYYYMMDD[_REF_referencia].pdf
        """
        if data is None:
            data = datetime.datetime.now().date()

        data_str = data.strftime("%Y%m%d")
        numero_instalacao = "".join(c for c in numero_instalacao if c.isalnum())

        if referencia:
            referencia_clean = "".join(
                c for c in referencia if c.isalnum() or c == "_"
            )
            return f"{credor_nome}_{numero_instalacao}_{data_str}_REF_{referencia_clean}.pdf"

        return f"{credor_nome}_{numero_instalacao}_{data_str}.pdf"

    def save_pdf(
        self,
        source_path: str,
        credor_nome: str,
        new_filename: Optional[str] = None,
        numero_instalacao: Optional[str] = None,
    ) -> str:
        """
        Salva um arquivo PDF no diretório apropriado do credor.

        Args:
            source_path: Caminho do arquivo PDF original.
            credor_nome: Nome do credor (ex: "DMAE", "RGE").
            new_filename: Novo nome para o arquivo. Se None, gera automaticamente.
            numero_instalacao: Número da instalação para geração de nome.

        Returns:
            Caminho completo do arquivo salvo.
        """
        credor_dir = self.get_credor_dir(credor_nome)

        if new_filename is None:
            if numero_instalacao:
                new_filename = self.generate_filename(credor_nome, numero_instalacao)
            else:
                new_filename = os.path.basename(source_path)

        new_filename = new_filename.removesuffix(".crdownload")

        if not new_filename.lower().endswith(".pdf"):
            new_filename += ".pdf"

        dest_path = os.path.join(credor_dir, new_filename)
        shutil.copy2(source_path, dest_path)
        logger.info("PDF salvo com sucesso: %s", dest_path)

        source_dir = os.path.dirname(source_path)
        if "downloads_temp" in source_dir or "documents" in source_dir:
            try:
                os.remove(source_path)
                logger.info("Arquivo original removido: %s", source_path)
            except OSError as e:
                logger.warning("Não foi possível remover o arquivo original: %s", e)

        return dest_path

    def file_to_base64(self, filepath: str) -> str:
        """
        Converte um arquivo para string base64.

        Args:
            filepath: Caminho do arquivo a ser convertido.

        Returns:
            String base64 do arquivo, ou string vazia em caso de erro.
        """
        if not os.path.exists(filepath):
            logger.error("Arquivo não encontrado para conversão base64: %s", filepath)
            return ""

        try:
            with open(filepath, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except OSError as e:
            logger.error("Erro ao converter arquivo para base64: %s", e)
            return ""

    def get_pdf_metadata(self, filepath: str) -> Optional[Dict]:
        """
        Obtém metadados de um arquivo.

        Args:
            filepath: Caminho do arquivo.

        Returns:
            Dicionário com metadados ou None em caso de erro.
        """
        if not os.path.exists(filepath):
            logger.error("Arquivo não encontrado para metadados: %s", filepath)
            return None

        try:
            stats = os.stat(filepath)
            return {
                "tamanho_bytes": stats.st_size,
                "tamanho_formatado": self._format_size(stats.st_size),
                "data_criacao": datetime.datetime.fromtimestamp(stats.st_ctime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "data_modificacao": datetime.datetime.fromtimestamp(stats.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "caminho_completo": os.path.abspath(filepath),
                "nome_arquivo": os.path.basename(filepath),
            }
        except OSError as e:
            logger.error("Erro ao obter metadados: %s", e)
            return None

    def listar_arquivos_recentes(self, pasta: str, minutos: int = 30) -> List[str]:
        """
        Lista arquivos modificados nos últimos X minutos em uma pasta.

        Args:
            pasta: Diretório a ser verificado.
            minutos: Janela de tempo em minutos.

        Returns:
            Lista de caminhos absolutos dos arquivos recentes.
        """
        limite = datetime.datetime.now() - datetime.timedelta(minutes=minutos)
        resultado = []

        for nome in os.listdir(pasta):
            caminho = os.path.join(pasta, nome)
            if os.path.isfile(caminho):
                modificado_em = datetime.datetime.fromtimestamp(os.path.getmtime(caminho))
                if modificado_em >= limite:
                    resultado.append(caminho)

        return resultado

    def limpar_arquivos_antigos(self, pasta: str, dias: int = 7) -> int:
        """
        Remove arquivos com data de modificação mais antiga que X dias.

        Args:
            pasta: Diretório a ser limpo.
            dias: Arquivos modificados há mais de X dias serão removidos.

        Returns:
            Número de arquivos removidos.
        """
        limite = datetime.datetime.now() - datetime.timedelta(days=dias)
        removidos = 0

        for nome in os.listdir(pasta):
            caminho = os.path.join(pasta, nome)
            if os.path.isfile(caminho):
                modificado_em = datetime.datetime.fromtimestamp(os.path.getmtime(caminho))
                if modificado_em < limite:
                    try:
                        os.remove(caminho)
                        removidos += 1
                        logger.info("Arquivo removido: %s", nome)
                    except OSError as e:
                        logger.warning("Erro ao remover arquivo %s: %s", nome, e)

        return removidos

    @staticmethod
    def _format_size(size_bytes: float) -> str:
        """Formata tamanho em bytes para formato legível (B, KB, MB, GB, TB)."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
