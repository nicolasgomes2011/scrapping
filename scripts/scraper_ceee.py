#!/usr/bin/env python3
import base64
import datetime
import json
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Garante que o diretório raiz do projeto esteja no sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.pdf_manager import PDFManager


def baixarDocumentoCEEE(matricula, cnpj):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    # Configuração para download de arquivos
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    pasta_downloads = os.path.join(project_root, "downloads_temp")
    os.makedirs(pasta_downloads, exist_ok=True)
    
    # Configura as preferências para download
    prefs = {
        "download.default_directory": pasta_downloads,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": False,
        "download.open_pdf_in_system_reader": False,
        "safebrowsing.enabled": False,
        "browser.helperApps.neverAsk.saveToDisk": "application/pdf",
        "browser.download.manager.showWhenStarting": False,
        "pdfjs.disabled": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    arquivos_baixados = []
    
    try:
        driver.get("https://rs.equatorialenergia.com.br/login")

        if not matricula:
            print("Matricula não informada.")
        else:
            matricula_input = wait.until(
                EC.visibility_of_element_located((By.ID, "matricula"))
            )
            matricula_input.send_keys(matricula)
            
           # Clica no botão da matrícula
            submit_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn-ok"))
            )
            print("Preenchi a matricula")
            
            submit_button.click()
            time.sleep(5)
            print("Cliquei no primeiro submit")

            # Preenche o campo CNPJ
            input_cnpj = driver.find_element(By.NAME, "cpfCnpjSolicitante")
            input_cnpj.send_keys(cnpj)
            
            submit_button_cnpj = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#solicitarDigitoCpfCnpj form[name='ExibirServicosPortalDmaeActionForm'] fieldset .btn-ok"))
            )
            submit_button_cnpj.click()
            
            #direcionar o usuário para o link emitirSegundaViaContaPortalDmaeAction.do
            driver.get("https://dmaeagvrt.procempa.com.br/gsan/emitirSegundaViaContaPortalDmaeAction.do")
            
            botao_imprimir = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[@title='Imprimir Fatura']"))
            )
            botao_imprimir.click()
            
            # Aguarda o download do arquivo
            time.sleep(5)
            
            # Verifica se algum arquivo foi baixado
            arquivos = [f for f in os.listdir(pasta_downloads) if not f.endswith('.crdownload')]
            
            if arquivos:
                # Inicializa o gerenciador de PDFs
                pdf_manager = PDFManager()
                
                for arquivo in arquivos:
                    caminho_arquivo = os.path.join(pasta_downloads, arquivo)
                    
                    # Salva o arquivo no diretório do credor usando o PDFManager
                    nome_arquivo = f"CEEE_{matricula}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
                    caminho_salvo = pdf_manager.save_pdf(caminho_arquivo, "CEEE", nome_arquivo)
                    
                    arquivos_baixados.append({
                        "arquivo_original": caminho_arquivo,
                        "arquivo_salvo": caminho_salvo
                    })
                    
                    print(f"Arquivo salvo com sucesso: {caminho_salvo}")
            else:
                print("Nenhum arquivo foi baixado.")
        
        return arquivos_baixados
    except Exception as e:
        print("Ocorreu um erro:", e)
        raise
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"status": "erro", "mensagem": "Uso: scraper_ceee.py <matricula> <cnpj>"}))
        sys.exit(1)

    codigo_imovel = sys.argv[1]
    cnpj = sys.argv[2]

    try:
        arquivos = baixarDocumentoCEEE(codigo_imovel, cnpj)

        for arquivo in arquivos:
            if arquivo.get("arquivo_salvo"):
                with open(arquivo["arquivo_salvo"], "rb") as f:
                    arquivo["pdf_base64"] = base64.b64encode(f.read()).decode("utf-8")

        print(json.dumps({"status": "sucesso", "arquivos": arquivos}))
    except Exception as e:
        print(json.dumps({"status": "erro", "mensagem": str(e)}))
