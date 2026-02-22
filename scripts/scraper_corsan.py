#!/usr/bin/env python3
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import time
import base64
import json
import shutil

# Define o diretório raiz do projeto (mesmo padrão do DMAE e RGE)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Função para converter arquivo para base64 - EXATAMENTE como no RGE e DMAE
def file_to_base64(filepath):
    try:
        import base64
        if not os.path.exists(filepath):
            print(f"ERRO: Arquivo não encontrado: {filepath}")
            return ""
        
        print(f"Convertendo arquivo para base64: {filepath}")
        with open(filepath, "rb") as f:
            content = base64.b64encode(f.read()).decode('utf-8')
            print(f"Base64 gerado com {len(content)} caracteres")
            return content
    except Exception as e:
        print(f"Erro ao converter para base64: {e}")
        return ""

# Implementação de PDFManager - similar ao RGE e DMAE
class PDFManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = os.path.join(project_root, "pdfs")
        else:
            self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        print(f"PDFManager iniciado. Diretório base: {self.base_dir}")

    def save_pdf(self, source_path, credor_nome, new_filename=None):
        try:
            credor_dir = os.path.join(self.base_dir, credor_nome.upper())
            os.makedirs(credor_dir, exist_ok=True)
            
            if new_filename is None:
                new_filename = os.path.basename(source_path)
            
            # Limpeza de nomes de arquivo
            if new_filename.endswith('.crdownload'):
                new_filename = new_filename[:-11]
            if not new_filename.lower().endswith('.pdf'):
                new_filename += '.pdf'
            
            dest = os.path.join(credor_dir, new_filename)
            print(f"Salvando PDF: {source_path} -> {dest}")
            
            # Copiar arquivo
            shutil.copy2(source_path, dest)
            
            # Tentar limpar o arquivo temporário
            try:
                source_dir = os.path.dirname(source_path)
                if "downloads_temp" in source_dir or "documents" in source_dir:
                    # Apenas remove se estiver em diretório temporário
                    os.remove(source_path)
                    print(f"Arquivo temporário removido: {source_path}")
            except Exception as e:
                print(f"Aviso: Não foi possível remover arquivo temporário: {e}")
            
            return dest
        except Exception as e:
            print(f"Erro ao salvar PDF: {e}")
            return source_path

def obter_mes_atual():
    return datetime.now().strftime("%m/%Y")

def baixar_documento(driver, wait, mes=None):
    try:
        # seu código anterior para baixar conta
        # ...

        # agora clica no botão "EMITIR 2ª VIA"
        botao_2via = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='EMITIR']/.."))
        )
        botao_2via.click()
        print("Botão 'EMITIR 2ª VIA' clicado com sucesso!")

    except TimeoutException:
        print("Botão 'EMITIR 2ª VIA' não encontrado ou não clicável.")

def login_corsan_e_baixar_documento(username, password, matricula=False, mes=obter_mes_atual(), pasta_downloads=None, pdf_manager=None):
    options = Options()
    options.headless = True  # Executa em modo headless para servidor
    options.add_argument('--headless=new')  # Comentado para debug

    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    # Configurar pasta de downloads se fornecida
    if pasta_downloads:
        prefs = {
            "download.default_directory": pasta_downloads,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": False,
            "download.open_pdf_in_system_reader": False,
            "browser.helperApps.neverAsk.saveToDisk": "application/pdf",
            "browser.download.manager.showWhenStarting": False,
            "pdfjs.disabled": True
        }
        options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    
    # Armazenar arquivos baixados
    arquivos_baixados = []

    try:
        driver.get("https://cliente.corsan.com.br/entrar")
        time.sleep(0.5)
        print("Acessando página da CORSAN")
        
        if not matricula:
            # Fluxo para login com usuário e senha
            botao = driver.find_element(By.CLASS_NAME, "botao-entrar")
            botao.click()

            login_input = wait.until(
                EC.visibility_of_element_located((By.ID, "signInName"))
            )
            login_input.send_keys(username)

            password_input = wait.until(
                EC.visibility_of_element_located((By.ID, "password"))
            )
            password_input.send_keys(password)

            button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            button.click()
        else:
            # Fluxo para acesso com CPF/CNPJ e matrícula - SEM captcha
            try:
                # Preenche os campos de CPF/CNPJ e matrícula
                driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='cpf_cnpj']").send_keys(username)
                driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='matricula']").send_keys(matricula)
                print(f"Campos preenchidos com CPF/CNPJ: {username} e Matrícula: {matricula}")

                # Tenta clicar no botão Consultar
                time.sleep(1)  # Pequena pausa para garantir que os campos foram preenchidos
                
                try:
                    # Tenta encontrar e clicar no botão de consulta
                    btn_consultar = driver.find_element(By.CLASS_NAME, "botao-consulta")
                    # Verifica se o botão está desabilitado e tenta habilitar
                    if btn_consultar.get_attribute("disabled"):
                        driver.execute_script("arguments[0].removeAttribute('disabled')", btn_consultar)
                    
                    # Clica usando JavaScript para evitar problemas
                    driver.execute_script("arguments[0].click();", btn_consultar)
                    print("Botão 'Consultar' clicado com sucesso.")
                except Exception as e:
                    print(f"Erro ao clicar no botão consultar: {e}")
                    # Tenta alternativa de busca pelo botão
                    btns = driver.find_elements(By.TAG_NAME, "button")
                    for btn in btns:
                        if "consult" in btn.text.lower():
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"Clicado em botão alternativo: {btn.text}")
                            break
            except Exception as e:
                print(f"Erro ao preencher formulário: {e}")
                return False  # Falha ao preencher formulário
                
        # Espera para verificar se chegamos à página de segunda via
        time.sleep(0.5)
        paginaAtual = driver.current_url
        print(f"URL atual: {paginaAtual}")
        
        if "segunda-via-rapida" in paginaAtual:
            print("Entrei na pagina de segunda via, através da matricula")
            
            try:
                # Tenta localizar e clicar no botão EMITIR 2ª VIA
                botao_2via = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='EMITIR 2ª VIA']/.."))
                )
                # Clica usando JavaScript
                driver.execute_script("arguments[0].click();", botao_2via)
                print("Botão 'EMITIR 2ª VIA' clicado com sucesso!")
                
                # Aguarda download do PDF
                time.sleep(1)
                return True  # Login e download bem-sucedidos
            except TimeoutException:
                print("Botão 'EMITIR 2ª VIA' não encontrado ou não clicável.")
                # Tenta alternativa
                try:
                    btns = driver.find_elements(By.TAG_NAME, "button")
                    for btn in btns:
                        if "emitir" in btn.text.lower() or "via" in btn.text.lower():
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"Clicado em botão alternativo: {btn.text}")
                            time.sleep(1)
                            return True  # Alternativa bem-sucedida
                            break
                except:
                    print("Não foi possível encontrar botões alternativos")
                    return False  # Falha em todas as tentativas
        else:
            print("Não foi possível acessar a página de segunda via")
            return False  # Falha ao acessar a página correta

    except Exception as e:
        print("Ocorreu um erro:", e)
        return False  # Falha com exceção
    finally:
        time.sleep(1)
        driver.quit()

def executar_scraper_corsan(cpf_cnpj, numero_instalacao):
    """
    Executa o scraper para obter documentos da CORSAN.
    
    Args:
        cpf_cnpj (str): CPF ou CNPJ do cliente
        numero_instalacao (str): Código de instalação/matrícula da CORSAN
    
    Returns:
        dict: Dicionário com arquivos baixados e métricas
    """
    tempo_inicio_total = time.time()
    print(f"[{datetime.now()}] Iniciando scraper CORSAN")
    
    # Configurações para o Chrome em modo headless
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    # Define pasta para downloads - IGUAL AO RGE E DMAE
    pasta_downloads = os.path.join(project_root, "downloads_temp")
    os.makedirs(pasta_downloads, exist_ok=True)
    
    # Inicializa o gerenciador de PDFs
    pdf_manager = PDFManager()
    
    prefs = {
        "download.default_directory": pasta_downloads,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": False,
        "download.open_pdf_in_system_reader": False,
        "safebrowsing.enabled": False,
        "browser.helperApps.neverAsk.saveToDisk": "application/pdf",
        "browser.download.manager.showWhenStarting": False,
        "pdfjs.disabled": True  # Desativa o visualizador de PDF interno
    }
    options.add_experimental_option("prefs", prefs)
    
    arquivos_baixados = []
    
    try:
        # Chama a função existente com os parâmetros da API
        login_sucesso = login_corsan_e_baixar_documento(
            cpf_cnpj, 
            "", 
            matricula=numero_instalacao, 
            pasta_downloads=pasta_downloads,
            pdf_manager=pdf_manager
        )
        
        # Se o login falhou, retornar estrutura vazia padronizada
        if not login_sucesso:
            print("Falha no login ou acesso à CORSAN. Não foi possível baixar documentos.")
            return {"arquivos": [], "metricas": {"erro": "Falha no login ou acesso à CORSAN"}}
        
        # Verifica se algum arquivo foi baixado
        arquivos_no_diretorio = [f for f in os.listdir(pasta_downloads) if f.endswith('.pdf')]
        print(f"Arquivos encontrados no diretório: {arquivos_no_diretorio}")
        
        data_atual = datetime.now().strftime("%Y%m%d")  # Formato ano-mês-dia para ser ordenável
        
        for i, arquivo in enumerate(arquivos_no_diretorio, 1):
            arquivo_path = os.path.join(pasta_downloads, arquivo)
            
            # Nomear arquivo no padrão "CORSAN_CODIGO_DATA_i.pdf"
            nome_arquivo = f"CORSAN_{numero_instalacao}_{data_atual}_{i}.pdf"
            novo_nome = os.path.join(pasta_downloads, nome_arquivo)
            
            try:
                # Renomear o arquivo
                os.rename(arquivo_path, novo_nome)
                print(f"Arquivo renomeado: {arquivo} -> {nome_arquivo}")
                
                # Salvar usando PDFManager - salvando na pasta pdfs/CORSAN/
                caminho_salvo = pdf_manager.save_pdf(novo_nome, "CORSAN", nome_arquivo)
                print(f"PDF salvo em: {caminho_salvo}")
                
                # Converter para base64 - IGUAL AO RGE E DMAE
                conteudo_base64 = file_to_base64(caminho_salvo)
                print(f"Base64 gerado com {len(conteudo_base64)} caracteres")
                
                # Adicionar à lista com o mesmo formato do RGE e DMAE
                arquivo_baixado = {
                    "arquivo_original": nome_arquivo,
                    "arquivo_salvo": caminho_salvo,
                    "sequencia": i,
                    "tempo_download": f"{time.time() - tempo_inicio_total:.2f}s",
                    "pdf_base64": conteudo_base64  # Inclusão do base64
                }
                arquivos_baixados.append(arquivo_baixado)
            except Exception as e:
                print(f"Erro ao processar arquivo {arquivo}: {e}")
        
        # Se não encontrou arquivos, criar um exemplo como no RGE/DMAE
        if not arquivos_baixados:
            print("Nenhum arquivo PDF foi baixado.")
            return {"arquivos": [], "metricas": {"erro": "Nenhum arquivo PDF foi baixado"}}
        
        # Adiciona métricas 
        tempo_total = time.time() - tempo_inicio_total
        metricas = {
            "tempo_total": f"{tempo_total:.2f}s",
            "quantidade_faturas": len(arquivos_baixados),
            "tempo_medio_por_fatura": f"{tempo_total/max(1, len(arquivos_baixados)):.2f}s"
        }
        
        # Retorna no MESMO FORMATO do RGE e DMAE para compatibilidade
        return {"arquivos": arquivos_baixados, "metricas": metricas}
        
    except Exception as e:
        print(f"Erro no scraper CORSAN: {e}")
        import traceback
        traceback.print_exc()
        # Retorno padronizado em caso de erro
        return {"arquivos": [], "metricas": {"erro": str(e)}}

if __name__ == "__main__":
    # Processar argumentos da linha de comando
    if len(sys.argv) >= 3:
        cpf_cnpj = sys.argv[1]
        numero_instalacao = sys.argv[2]
        print(f"Executando com argumentos da linha de comando: CPF/CNPJ={cpf_cnpj}, Matrícula={numero_instalacao}", file=sys.stderr)
    else:
        # Valores padrão para testes
        cpf_cnpj = "13765133000109"
        numero_instalacao = "944033"
        print(f"Executando com valores padrão: CPF/CNPJ={cpf_cnpj}, Matrícula={numero_instalacao}", file=sys.stderr)

    try:
        # Executar o scraper e obter o resultado
        arquivos_baixados = executar_scraper_corsan(cpf_cnpj, numero_instalacao)
        
        # PROBLEMA CRÍTICO: Se arquivos_baixados não for um dicionário com a chave "arquivos",
        # precisa ser transformado antes de retornar
        if isinstance(arquivos_baixados, list):
            # Converte para o formato esperado pelo app.py
            tempo_total = time.time()
            resultado = {
                "arquivos": arquivos_baixados,
                "metricas": {
                    "tempo_total": f"{tempo_total:.2f}s",
                    "quantidade_faturas": len(arquivos_baixados),
                    "tempo_medio_por_fatura": f"{tempo_total/max(1, len(arquivos_baixados)):.2f}s"
                }
            }
        else:
            # Já está no formato correto
            resultado = arquivos_baixados
            
        # Verifica se há arquivos baixados mas nenhum tem base64
        if isinstance(resultado, dict) and "arquivos" in resultado and resultado["arquivos"]:
            for arquivo in resultado["arquivos"]:
                if "arquivo_salvo" in arquivo and "pdf_base64" not in arquivo:
                    # Adiciona base64 ao arquivo que não tem
                    print(f"Adicionando base64 faltante para: {arquivo['arquivo_salvo']}", file=sys.stderr)
                    arquivo["pdf_base64"] = file_to_base64(arquivo["arquivo_salvo"])
        
        # SOLUÇÃO DE CONTINGÊNCIA: Se não houver arquivos baixados, tenta buscar diretamente na pasta
        if not (isinstance(resultado, dict) and "arquivos" in resultado and resultado["arquivos"]):
            print("Nenhum arquivo baixado encontrado. Tentando buscar diretamente na pasta...", file=sys.stderr)
            pdf_dir = os.path.join(project_root, "pdfs", "CORSAN")
            if os.path.exists(pdf_dir):
                pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf') and numero_instalacao in f]
                if pdf_files:
                    # Encontrou arquivos direto na pasta
                    pdf_files.sort(reverse=True)  # Ordena do mais recente para o mais antigo
                    arquivos_recuperados = []
                    
                    for i, pdf_file in enumerate(pdf_files[:3], 1):  # Limita a 3 arquivos
                        pdf_path = os.path.join(pdf_dir, pdf_file)
                        # Converte para base64
                        base64_content = file_to_base64(pdf_path)
                        
                        arquivos_recuperados.append({
                            "arquivo_salvo": pdf_path,
                            "sequencia": i,
                            "pdf_base64": base64_content,
                            "recuperado_de": "busca_direta_pasta"
                        })
                    
                    # Retorna os arquivos recuperados
                    resultado = {
                        "arquivos": arquivos_recuperados,
                        "metricas": {
                            "recuperado_por": "busca_direta_pasta",
                            "quantidade_arquivos": len(arquivos_recuperados)
                        }
                    }
        
        # IMPORTANTE: Imprime APENAS o JSON sem texto adicional - IGUAL AO RGE E DMAE
        print(json.dumps(resultado))
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Em caso de erro, retornar um JSON vazio mas válido - IGUAL AO RGE E DMAE
        print(json.dumps({"arquivos": [], "metricas": {"erro": str(e)}}))
