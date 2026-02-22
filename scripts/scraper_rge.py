#!/usr/bin/env python3
import os
import sys
import time
import glob
import datetime
import json
import shutil
import importlib.util

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

#essa função será responsável somente por fazer o login, será usada posteriormente em todos os scrapers.
def fazerLogin(usuario, senha, idInputLogin, idInputSenha, Seletor, driver, wait):
    try:
            username_field = driver.find_element(By.ID, idInputLogin)
            username_field.send_keys(usuario)
    except:
        campos_texto = driver.find_elements(By.TAG_NAME, "input")
        for campo in campos_texto:
            if campo.get_attribute("type") in ["text", "email"]:
                campo.send_keys(usuario)
                break

    try:
        password_field = driver.find_element(By.ID, idInputSenha)
        password_field.send_keys(senha)
    except:
        campos = driver.find_elements(By.TAG_NAME, "input")
        for campo in campos:
            if campo.get_attribute("type") == "password":
                campo.send_keys(senha)
                break
    

def load_pdf_manager_class():
    """
    Tenta importar PDFManager de diferentes formas:
    1) import pdf_manager (com PYTHONPATH ajustado)
    2) carregar por caminho (importlib.util.spec_from_file_location)
    3) fallback: classe mínima que funciona silenciosamente
    """
    try:
        # tenta importar normalmente (se o project_root estiver no sys.path)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        import pdf_manager as pm
        return pm.PDFManager
    except Exception:
        try:
            # tenta carregar diretamente do arquivo
            module_path = os.path.join(project_root, 'pdf_manager.py')
            if os.path.exists(module_path):
                spec = importlib.util.spec_from_file_location("pdf_manager", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return getattr(module, 'PDFManager')
        except Exception:
            pass

    # fallback mínimo (silencioso)
    class PDFManager:
        def __init__(self, base_dir=None):
            if base_dir is None:
                self.base_dir = os.path.join(project_root, "pdfs")
            else:
                self.base_dir = base_dir
            os.makedirs(self.base_dir, exist_ok=True)

        def save_pdf(self, source_path, credor_nome, new_filename=None):
            try:
                credor_dir = os.path.join(self.base_dir, credor_nome.upper())
                os.makedirs(credor_dir, exist_ok=True)
                if new_filename is None:
                    new_filename = os.path.basename(source_path)
                if new_filename.endswith('.crdownload'):
                    new_filename = new_filename[:-11]
                if not new_filename.lower().endswith('.pdf'):
                    new_filename += '.pdf'
                dest = os.path.join(credor_dir, new_filename)
                shutil.copy2(source_path, dest)
                try:
                    source_dir = os.path.dirname(source_path)
                    if "downloads_temp" in source_dir:
                        os.remove(source_path)
                except:
                    pass
                return dest
            except:
                return source_path

        def file_to_base64(self, filepath):
            try:
                import base64
                if not os.path.exists(filepath):
                    return ""
                with open(filepath, "rb") as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except:
                return ""

    return PDFManager

PDFManagerClass = load_pdf_manager_class()

def fechar_modal(driver, wait):
    try:
        wait_curto = WebDriverWait(driver, 2)
        modal_close_btn = wait_curto.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-close-button"))
        )
        modal_close_btn.click()
        time.sleep(0.5)
    except:
        pass

def fechar_popup_cookies(driver, wait):
    try:
        wait_curto = WebDriverWait(driver, 2)
        cookie_close_btn = wait_curto.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.onetrust-close-btn-handler"))
        )
        cookie_close_btn.click()
        time.sleep(0.5)
    except:
        pass

def baixar_documento(driver, wait):
    try:
        wait_curto = WebDriverWait(driver, 3)
        btn_baixar = wait_curto.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.entenda-conta"))
        )
        driver.execute_script("arguments[0].click();", btn_baixar)
        time.sleep(1)
        return True
    except:
        # alternativa simples: tentar clicar em links/botoes que contenham palavras relacionadas
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute('href') or ''
                text = (link.text or '').lower()
                if any(k in href.lower() or k in text for k in ('pdf','fatura','segunda via','download','baixar','conta')):
                    try:
                        driver.execute_script("arguments[0].click();", link)
                        time.sleep(2)
                        return True
                    except:
                        continue
        except:
            pass
        return False

def login_rge_e_seleciona_instalacao(username, password, informacoes={}):
    options = Options()
    options.headless = True
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--dns-prefetch-disable')
    options.add_argument('--disable-features=NetworkService')
    options.add_argument('--disable-proxy-certificate-handler')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    pasta_downloads = os.path.join(project_root, "downloads_temp")
    os.makedirs(pasta_downloads, exist_ok=True)

    prefs = {
        "download.default_directory": os.path.abspath(pasta_downloads),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": False
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    wait = WebDriverWait(driver, 5)

    try:
        driver.get("https://www.rge-rs.com.br")
        sign_in_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".sign-in-text a")))
        driver.execute_script("arguments[0].click();", sign_in_button)
        time.sleep(1)

        # campos podem variar, tentamos preencher
        try:
            username_field = driver.find_element(By.ID, "signInName")
            username_field.send_keys(username)
        except:
            campos_texto = driver.find_elements(By.TAG_NAME, "input")
            for campo in campos_texto:
                if campo.get_attribute("type") in ["text", "email"]:
                    campo.send_keys(username)
                    break

        try:
            password_field = driver.find_element(By.ID, "password")
            password_field.send_keys(password)
        except:
            campos = driver.find_elements(By.TAG_NAME, "input")
            for campo in campos:
                if campo.get_attribute("type") == "password":
                    campo.send_keys(password)
                    break

        try:
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            driver.execute_script("arguments[0].click();", login_button)
        except:
            botoes = driver.find_elements(By.TAG_NAME, "button")
            for botao in botoes:
                if "entrar" in (botao.text or "").lower() or "login" in (botao.text or "").lower():
                    driver.execute_script("arguments[0].click();", botao)
                    break

        time.sleep(1.5)
        fechar_modal(driver, wait)

        if "area-cliente" not in driver.current_url:
            driver.get("https://www.rge-rs.com.br/area-cliente/cadastro")
            time.sleep(1)

        fechar_popup_cookies(driver, wait)
        try:
            # Tentativa por ID específico
            instalacao_id = f"instalacao-{informacoes.get('instalacao')}"
            radio = driver.find_element(By.ID, instalacao_id)
            driver.execute_script("arguments[0].click();", radio)
        except:
            # Tentativa por seleção de qualquer radio button
            try:
                radios = driver.find_elements(By.NAME, "instalacao")
                if radios:
                    driver.execute_script("arguments[0].click();", radios[0])
            except:
                pass
        
        # Tenta clicar no botão Buscar
        try:
            btn_buscar = driver.find_element(By.ID, "btn-buscar")
            driver.execute_script("arguments[0].click();", btn_buscar)
        except:
            # Tenta encontrar qualquer botão de busca
            botoes = driver.find_elements(By.TAG_NAME, "button")
            for botao in botoes:
                if "buscar" in botao.text.lower():
                    driver.execute_script("arguments[0].click();", botao)
                    break
        
        fechar_modal(driver, wait)
        time.sleep(1)
        baixar_documento(driver, wait)

        novos_arquivos = [f for f in os.listdir(pasta_downloads) if f.endswith('.pdf')]
        return novos_arquivos
    except:
        return []
    finally:
        try:
            driver.quit()
        except:
            pass

def file_to_base64(filepath):
    try:
        import base64
        if not os.path.exists(filepath):
            return ""
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return ""

def executar_scraper_rge(usuario, senha, numero_instalacao, cpf_cnpj):
    tempo_inicio_total = time.time()
    pasta_downloads = os.path.join(project_root, "downloads_temp")
    os.makedirs(pasta_downloads, exist_ok=True)

    pasta_pdfs = os.path.join(project_root, "pdfs", "RGE")
    os.makedirs(pasta_pdfs, exist_ok=True)

    pdf_manager = PDFManagerClass()

    arquivos_baixados = []
    arquivos_antes = set([f for f in os.listdir(pasta_downloads) if f.endswith('.pdf')])

    informacoes = {"instalacao": numero_instalacao}
    novos_arquivos = login_rge_e_seleciona_instalacao(usuario, senha, informacoes)

    arquivos_depois = set([f for f in os.listdir(pasta_downloads) if f.endswith('.pdf')])
    arquivos_novos = arquivos_depois - arquivos_antes

    if not arquivos_novos and novos_arquivos:
        arquivos_novos = set(novos_arquivos)

    for i, arquivo in enumerate(arquivos_novos, start=1):
        try:
            arquivo_path = os.path.join(pasta_downloads, arquivo)
            if not os.path.exists(arquivo_path):
                continue

            nome_arquivo = f"RGE_{numero_instalacao}_{datetime.datetime.now().strftime('%Y%m%d')}_{i}.pdf"
            caminho_salvo = pdf_manager.save_pdf(arquivo_path, "RGE", nome_arquivo)

            conteudo_base64 = file_to_base64(caminho_salvo)

            arquivos_baixados.append({
                "arquivo_original": arquivo_path,
                "arquivo_salvo": caminho_salvo,
                "sequencia": i,
                "tempo_download": f"{time.time() - tempo_inicio_total:.2f}s",
                "pdf_base64": conteudo_base64
            })
        except:
            pass

    if not arquivos_baixados:
        print('Nenhum arquivo PDF foi baixado ou encontrado.')

    tempo_total = time.time() - tempo_inicio_total
    metricas = {
        "tempo_total": f"{tempo_total:.2f}s",
        "quantidade_faturas": len(arquivos_baixados),
        "tempo_medio_por_fatura": f"{tempo_total/max(1, len(arquivos_baixados)):.2f}s"
    }

    resultado_final = {"arquivos": arquivos_baixados, "metricas": metricas}
    return resultado_final

if __name__ == "__main__":
    try:
        if len(sys.argv) >= 5:
            usuario = sys.argv[3]
            senha = sys.argv[4]
            numero_instalacao = sys.argv[1]
            cpf_cnpj = sys.argv[2]
            resultado = executar_scraper_rge(usuario, senha, numero_instalacao, cpf_cnpj)
            # imprime apenas o JSON no stdout
            print(json.dumps(resultado))
        else:
            print(json.dumps({"arquivos": [], "metricas": {}, "erro": "Parâmetros inválidos"}))
            sys.exit(1)
    except Exception as e:
        # em caso de erro imprime um JSON com a chave "erro"
        try:
            print(json.dumps({"arquivos": [], "metricas": {}, "erro": str(e)}))
        except:
            print(json.dumps({"arquivos": [], "metricas": {}, "erro": "erro inesperado"}))
        sys.exit(1)
