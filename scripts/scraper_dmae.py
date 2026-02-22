#!/usr/bin/env python3
import os
import sys
import time
import glob
import datetime
import json
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define o diretório raiz do projeto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Função para converter arquivo para base64 - EXATAMENTE como no RGE
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

# Implementação de PDFManager - similar ao RGE
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

def executar_scraper_dmae(numero_instalacao, cpf_cnpj):
    """
    Executa o scraper para obter documentos do DMAE.
    
    Args:
        numero_instalacao (str): Código de instalação/matrícula do DMAE
        cpf_cnpj (str): CPF ou CNPJ do cliente
    
    Returns:
        dict: Dicionário com arquivos baixados e métricas
    """
    tempo_inicio_total = time.time()
    print(f"[{datetime.datetime.now()}] Iniciando scraper DMAE com instalação: {numero_instalacao} e CPF/CNPJ: {cpf_cnpj}")
    
    options = Options()
    # Desativar headless temporariamente para depuração (ativar depois)
    options.headless = True  # Executa em modo headless para servidor
    options.add_argument('--headless=new')

    options.add_argument("--headless")  # se quiser rodar sem abrir janela

    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-print-preview')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument("--lang=pt-BR")
    options.add_argument("accept-language=pt-BR,pt;q=0.9")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    # antes de instanciar o driver:
    options.add_experimental_option("prefs", {"intl.accept_languages": "pt-BR,pt"})
    options.add_argument("--lang=pt-BR")


    
    # Pasta de downloads -> temporária no mesmo formato que o RGE
    pasta_downloads = os.path.join(project_root, "downloads_temp")
    os.makedirs(pasta_downloads, exist_ok=True)

    # Inicializa o gerenciador de PDFs
    pdf_manager = PDFManager()

    # Limpeza prévia para evitar confusão com arquivos antigos
    for arquivo in os.listdir(pasta_downloads):
        if arquivo.endswith('.crdownload') or arquivo.endswith('.tmp'):
            try:
                os.remove(os.path.join(pasta_downloads, arquivo))
                print(f"Arquivo temporário removido: {arquivo}")
            except Exception as e:
                print(f"Não foi possível remover arquivo temporário: {e}")

    prefs = {
        "download.default_directory": pasta_downloads,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        # Permitir abrir PDFs externamente - mudamos para TRUE
        "plugins.always_open_pdf_externally": True,
        # Baixar PDFs automaticamente
        "download.open_pdf_in_system_reader": True,
        "safebrowsing.enabled": False,
        # Definir comportamento para tipos de conteúdo
        "download.default_directory": os.path.abspath(pasta_downloads),
        "browser.helperApps.neverAsk.saveToDisk": "application/pdf",
        "browser.download.manager.showWhenStarting": False,
        # Habilitar visualizador de PDF - mudamos para FALSE
        "pdfjs.disabled": False
    }
    options.add_experimental_option("prefs", prefs)

    tempo_inicio_driver = time.time()
    driver = webdriver.Chrome(options=options)
    
    # força o header Accept-Language via DevTools (Selenium 4+)
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {"Accept-Language": "pt-BR,pt;q=0.9"}
    })
    
    print(f"Inicialização do driver: {time.time() - tempo_inicio_driver:.2f}s")
    driver.set_page_load_timeout(60)  # Define um timeout para carregar páginas
    
    # Aumentamos o timeout para 30 segundos
    wait = WebDriverWait(driver, 60)
    arquivos_baixados = []
    
    try:
        # Navegação para página inicial
        tempo_inicio_navegacao = time.time()
        print("Tentando acessar a página inicial do DMAE...")
        
        # Tenta acessar a página com tratamento de exceções
        try:
            driver.get("https://dmaeagvrt.procempa.com.br/gsan/exibirServicosPortalDmaeAction.do")
            print(f"URL após tentativa de acesso: {driver.current_url}")
            
            # Verifica se carregou a página correta
            if "procempa" not in driver.current_url:
                print("ALERTA: Redirecionado para URL inesperada")
                # Tenta novamente
                driver.get("https://dmaeagvrt.procempa.com.br/gsan/exibirServicosPortalDmaeAction.do")
                time.sleep(3)
        except Exception as e:
            print(f"Erro ao carregar página inicial: {e}")
            # Tenta uma URL alternativa
            try:
                driver.get("https://dmaeagvrt.procempa.com.br/")
                time.sleep(3)
                print(f"Carregando URL alternativa: {driver.current_url}")
            except:
                print("Falha ao carregar URL alternativa também")
        
        print(f"Carregamento da página inicial: {time.time() - tempo_inicio_navegacao:.2f}s")
        print(f"URL atual: {driver.current_url}")
        print(f"Título da página: {driver.title}")
        
        driver.save_screenshot("step1_home.png")
        with open("step1_home.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Tenta clicar em qualquer link que possa levar à página de matrícula
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"Encontrados {len(links)} links na página")
            for link in links[:5]:  # Mostrar apenas os primeiros 5 para debug
                print(f"Link: {link.text} - {link.get_attribute('href')}")
            
            # Tenta encontrar um link para a página de matrícula
            for link in links:
                if "matricula" in link.get_attribute('href').lower() or "servicos" in link.get_attribute('href').lower():
                    print(f"Clicando em link potencial: {link.text}")
                    link.click()
                    time.sleep(3)
                    break
        except Exception as e:
            print(f"Erro ao analisar links: {e}")
        
        # Verifica novamente a URL após possível navegação
        print(f"URL após tentativa de navegação: {driver.current_url}")
        
        # --- fluxo normal DMAE ---
        tempo_inicio_form = time.time()
        try:
            # Primeiro tenta localizar o campo de matrícula
            print("Procurando campo de matrícula...")
            
            # Tenta diferentes métodos para localizar o campo
            try:
                matricula_input = wait.until(
                    EC.visibility_of_element_located((By.ID, "matricula"))
                )
            except:
                # Tenta XPath mais genérico
                try:
                    matricula_input = driver.find_element(By.XPATH, "//input[contains(@id, 'matricula') or contains(@name, 'matricula')]")
                except:
                    # Tenta qualquer campo input visível
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    for input_elem in inputs:
                        if input_elem.is_displayed():
                            print(f"Campo input encontrado: {input_elem.get_attribute('id')} - {input_elem.get_attribute('name')}")
                            if not input_elem.get_attribute('type') == 'hidden':
                                matricula_input = input_elem
                                break
            
            print(f"Campo de matrícula encontrado: {matricula_input}")
            # Limpa o campo e insere o valor
            matricula_input.clear()
            matricula_input.send_keys(numero_instalacao)
            print(f"Número de instalação inserido: {numero_instalacao}")
            
            # Tenta localizar o botão de envio
            print("Procurando botão de envio...")
            try:
                submit_button = wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "btn-ok"))
                )
            except:
                # Tenta XPath mais genérico
                try:
                    submit_button = driver.find_element(By.XPATH, "//input[@type='submit' or @type='button']")
                except:
                    # Tenta qualquer botão
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    if buttons:
                        submit_button = buttons[0]
                    else:
                        # Último recurso: tenta Enter no campo de matrícula
                        matricula_input.send_keys("\n")
                        submit_button = None
            
            if submit_button:
                # Tenta JavaScript para clicar no botão
                driver.execute_script("arguments[0].click();", submit_button)
                print("Botão clicado via JavaScript")
            
            print(f"Envio do primeiro formulário: {time.time() - tempo_inicio_form:.2f}s")
            print(f"URL após envio do primeiro formulário: {driver.current_url}")
            
            # Após submeter o formulário, faça uma pausa para garantir carregamento
            time.sleep(0.5)
            
            # Debug
            print(f"Título após primeiro formulário: {driver.title}")
            
            # Espera pelo próximo elemento - campo de CNPJ
            tempo_inicio_cnpj = time.time()
            try:
                input_cnpj = wait.until(
                    EC.visibility_of_element_located((By.NAME, "cpfCnpjSolicitante"))
                )
                print(f"Campo CNPJ encontrado: {time.time() - tempo_inicio_cnpj:.2f}s")
                
                # Limpa o campo e insere o valor
                input_cnpj.clear()
                input_cnpj.send_keys(cpf_cnpj)
                print(f"CNPJ inserido: {cpf_cnpj}")
                
                # Tenta localizar o botão de envio do CNPJ
                try:
                    submit_button_cnpj = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "#solicitarDigitoCpfCnpj form[name='ExibirServicosPortalDmaeActionForm'] fieldset .btn-ok"))
                    )
                    # Clica via JavaScript
                    driver.execute_script("arguments[0].click();", submit_button_cnpj)
                    print("Botão de CNPJ clicado via JavaScript")
                except:
                    # Tenta XPath mais genérico
                    try:
                        submit_button_cnpj = driver.find_element(By.XPATH, "//input[@type='submit' or @type='button']")
                        driver.execute_script("arguments[0].click();", submit_button_cnpj)
                    except:
                        # Último recurso: tenta Enter no campo de CNPJ
                        input_cnpj.send_keys("\n")
                
                print(f"Envio do formulário CNPJ: {time.time() - tempo_inicio_cnpj:.2f}s")
                print(f"URL após envio do CNPJ: {driver.current_url}")
                
                # Após submeter o CNPJ, faça uma pausa para garantir carregamento
                time.sleep(1)
            except Exception as e:
                print(f"Erro ao processar campo CNPJ: {e}")
                # Se não conseguir encontrar o campo CNPJ, pode ser que já estejamos na próxima etapa
                print("Tentando prosseguir para a página de faturas...")
            
            # Navegação para página de faturas
            tempo_inicio_faturas = time.time()
            print("Navegando para página de faturas...")
            driver.get("https://dmaeagvrt.procempa.com.br/gsan/emitirSegundaViaContaPortalDmaeAction.do")
            
            # Aumentando tempo de espera para garantir carregamento completo da tabela
            time.sleep(10)  # Mantemos 3 segundos de espera
            print(f"URL da página de faturas: {driver.current_url}")
            
            # Debug: verificar e imprimir o HTML completo da página
            print("Analisando o HTML da página para encontrar links de faturas...")
            html_completo = driver.page_source
            
            # Tenta encontrar os links de impressão diretamente no HTML
            import re
            # Padrão regex para encontrar links de impressão de faturas no formato JavaScript
            pattern = r"javascript:abrirPopup\('(gerarRelatorio2ViaContaEGuiaPagamentoAction\.do\?identificadorContaEmail=[^']+)'[^)]*\)"
            matches = re.findall(pattern, html_completo)
            
            driver.save_screenshot("step4_faturas.png")
            with open("step4_faturas.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Encontrados {len(matches)} links de impressão usando regex")
            
            # Se encontrou links via regex
            if matches:
                print("Links encontrados via regex:")
                for i, match in enumerate(matches[:3]):  # Mostrar apenas os primeiros 3
                    print(f"  - {i+1}: {match}")
                
                # Construir URLs completas para acessar diretamente
                urls_faturas = [f"https://dmaeagvrt.procempa.com.br/gsan/{match}&lojaVirtual=S" for match in matches]
                botoes_imprimir = urls_faturas  # Usamos as URLs diretamente
            else:
                # Se não encontrou via regex, tenta o método antigo com seletores
                print("Tentando métodos alternativos para encontrar as faturas...")
                
                # Verifica se há tabelas
                tabelas = driver.find_elements(By.TAG_NAME, "table")
                print(f"Encontradas {len(tabelas)} tabelas na página")
                
                # Verifica se há uma tabela específica com "Mês / Ano da Fatura" no cabeçalho
                tabela_faturas = None
                for tabela in tabelas:
                    try:
                        if "Mês / Ano da Fatura" in tabela.text or "Imprimir" in tabela.text:
                            print("Tabela de faturas encontrada!")
                            tabela_faturas = tabela
                            print(f"Conteúdo da tabela: {tabela.text[:500]}")
                            break
                    except:
                        continue
                
                # Seletores baseados no HTML que você compartilhou
                seletores = [
                    "//img[@alt='Imprimir Fatura']/..",
                ]
                
                botoes_imprimir = []  # Inicializa como lista vazia, não como string 'null'
                for seletor in seletores:
                    try:
                        print(f"Tentando seletor: {seletor}")
                        elementos = driver.find_elements(By.XPATH, seletor)
                        if elementos:
                            print(f"Encontrados {len(elementos)} elementos com seletor {seletor}")
                            # Imprime mais detalhes sobre os elementos encontrados
                            for i, elem in enumerate(elementos[:3]):
                                href = elem.get_attribute('href') or ""
                                onclick = elem.get_attribute('onclick') or ""
                                print(f"  - Elemento {i+1}: href={href}, onclick={onclick}")
                            
                            # Verificação de elementos válidos
                            elementos_validos = []
                            for elem in elementos:
                                if elem.get_attribute('href') or elem.get_attribute('onclick'):
                                    elementos_validos.append(elem)
                            
                            if elementos_validos:
                                print(f"Elementos válidos encontrados: {len(elementos_validos)}")
                                botoes_imprimir = elementos_validos
                                break
                    except Exception as e:
                        print(f"Erro com seletor {seletor}: {e}")
            
            # Quantidade final de faturas encontradas
            quantidade_faturas = len(botoes_imprimir) if botoes_imprimir else 0
            print(f"Encontradas {quantidade_faturas} faturas para baixar.")
            
            # Obtém a data atual no formato AAAAMMDD para ordenação cronológica
            data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Só tenta baixar faturas se realmente houver botões ou URLs
            if botoes_imprimir and quantidade_faturas > 0:
                for i, botao in enumerate(botoes_imprimir, start=1):
                    tempo_inicio_download = time.time()
                    print(f"Iniciando download da fatura {i}...")

                    # Remove arquivos antigos antes do clique
                    antigos = set(os.listdir(pasta_downloads))
                    
                    # Verifica se estamos lidando com URLs (do regex) ou elementos
                    if isinstance(botao, str):
                        # Verifica se é uma URL válida antes de acessar
                        if botao.startswith('http'):
                            print(f"Acessando URL direta: {botao}")
                            driver.get(botao)
                        else:
                            print(f"URL inválida ignorada: {botao}")
                            continue
                    else:
                        # É um elemento WebElement - extrai o JavaScript ou href
                        href = botao.get_attribute('href')
                        onclick = botao.get_attribute('onclick')
                        
                        print(f"Processando elemento: href={href}, onclick={onclick}")
                        
                        if href and 'javascript:abrirPopup' in href:
                            # Extrai os parâmetros da função abrirPopup
                            match = re.search(r"abrirPopup\('([^']+)'", href)
                            if match:
                                popup_url = match.group(1)
                                # Constrói a URL completa
                                url_completa = f"https://dmaeagvrt.procempa.com.br/gsan/{popup_url}"
                                print(f"Extraída URL do popup: {url_completa}")
                                # Acessa diretamente
                                driver.get(url_completa)
                            else:
                                # Se não conseguiu extrair, tenta o clique JavaScript normal
                                print("Usando clique JavaScript padrão")
                                driver.execute_script("arguments[0].click();", botao)
                        elif onclick and 'abrirPopup' in onclick:
                            # Extrai os parâmetros da função abrirPopup do atributo onclick
                            match = re.search(r"abrirPopup\('([^']+)'", onclick)
                            if match:
                                popup_url = match.group(1)
                                # Constrói a URL completa
                                url_completa = f"https://dmaeagvrt.procempa.com.br/gsan/{popup_url}"
                                print(f"Extraída URL do popup via onclick: {url_completa}")
                                # Acessa diretamente
                                driver.get(url_completa)
                            else:
                                # Se não conseguiu extrair, tenta o clique JavaScript normal
                                print("Usando clique JavaScript padrão para onclick")
                                driver.execute_script("arguments[0].click();", botao)
                        elif href and href.startswith('http'):
                            # É um link direto
                            print(f"Acessando link direto: {href}")
                            driver.get(href)
                        else:
                            # Clique JavaScript normal como último recurso
                            print("Usando clique JavaScript como último recurso")
                            driver.execute_script("arguments[0].click();", botao)
                    
                    # Espera mais tempo para o download começar
                    time.sleep(10)
                    
                    # Espera o download terminar
                    if esperar_download(pasta_downloads, timeout=100):  # Aumentado para 20 segundos
                        # Pega o novo arquivo que apareceu
                        novos = set(os.listdir(pasta_downloads)) - antigos
                        if novos:
                            arquivo_baixado = os.path.join(pasta_downloads, list(novos)[0])
                            # Novo formato de nome: DMAE_CODIGO_DATA.pdf
                            nome_arquivo = f"DMAE_{numero_instalacao}_{data_atual}_{i}.pdf"
                            novo_nome = os.path.join(pasta_downloads, nome_arquivo)
                            os.rename(arquivo_baixado, novo_nome)
                            print(f"Fatura {i} salva como: {novo_nome}")
                            print(f"Tempo total de download da fatura {i}: {time.time() - tempo_inicio_download:.2f}s")
                            
                            # Processamento do arquivo baixado
                            tempo_inicio_salvamento = time.time()
                            caminho_salvo = pdf_manager.save_pdf(novo_nome, "DMAE", nome_arquivo)
                            print(f"Salvamento do PDF no diretório do credor: {time.time() - tempo_inicio_salvamento:.2f}s")
                            
                            # PARTE CRÍTICA: Converter para base64 - Idêntico ao RGE
                            tempo_inicio_base64 = time.time()
                            conteudo_base64 = file_to_base64(caminho_salvo)
                            print(f"Conversão para base64: {time.time() - tempo_inicio_base64:.2f}s")
                            
                            arquivos_baixados.append({
                                "arquivo_original": novo_nome,
                                "arquivo_salvo": caminho_salvo,
                                "sequencia": i,
                                "tempo_download": f"{time.time() - tempo_inicio_download:.2f}s",
                                "pdf_base64": conteudo_base64
                            })
                    else:
                        print(f"Timeout: download da fatura {i} não finalizou após 20 segundos.")
                        # Tentativa de forçar clique direto no link
                        try:
                            href = botao.get_attribute('href')
                            if href:
                                print(f"Tentando acessar diretamente a URL: {href}")
                                driver.get(href)
                                time.sleep(1)
                                if esperar_download(pasta_downloads, timeout=10):
                                    # Processar arquivo baixado
                                    print("Download concluído pela URL direta")
                                else:
                                    print("Falha também na abordagem direta")
                        except Exception as e:
                            print(f"Erro na tentativa alternativa: {e}")

            # IMPORTANTE: Criar um arquivo de exemplo se nenhum foi baixado
            if not arquivos_baixados:
                print("Nenhum arquivo foi baixado.")
                
            
            tempo_total = time.time() - tempo_inicio_total
            print(f"Todas as faturas foram baixadas! Tempo total: {tempo_total:.2f}s")
            
            # Adiciona informações de tempo ao retorno
            metricas = {
                "tempo_total": f"{tempo_total:.2f}s",
                "quantidade_faturas": quantidade_faturas,
                "tempo_medio_por_fatura": f"{tempo_total/max(1, quantidade_faturas):.2f}s" if quantidade_faturas > 0 else "0.00s"
            }
            
            # Formato IDÊNTICO ao RGE para compatibilidade perfeita
            resultado_final = {"arquivos": arquivos_baixados, "metricas": metricas}
            return resultado_final

        except Exception as e:
            print(f"Erro crítico no fluxo do DMAE: {e}")
            # Tenta capturar screenshot para diagnóstico
            try:
                screenshot_path = os.path.join(os.getcwd(), "dmae_error.png")
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot de erro salvo em: {screenshot_path}")
            except:
                print("Não foi possível salvar screenshot")
            raise
    
    finally:
        print("Fechando o driver...")
        driver.quit()
        print("Driver fechado com sucesso")

def esperar_download(pasta, timeout=15):
    """
    Espera até que todos os downloads terminem (sem .crdownload).
    Versão melhorada com detecção de novos arquivos.
    """
    segundos = 0
    inicio = time.time()
    arquivos_iniciais = set(os.listdir(pasta))
    
    while segundos < timeout:
        # Verificar arquivos .crdownload
        incompletos = [f for f in os.listdir(pasta) if f.endswith(".crdownload") or f.endswith(".tmp")]
        if not incompletos:
            # Verificar se apareceu algum arquivo novo
            arquivos_atuais = set(os.listdir(pasta))
            novos_arquivos = arquivos_atuais - arquivos_iniciais
            
            if novos_arquivos:
                print(f"Download completo em {time.time() - inicio:.2f} segundos. Novos arquivos: {novos_arquivos}")
                return True
            
            # Se não tem incompletos nem novos após 2 segundos, provável falha
            if segundos > 2:
                print("Nenhum download parece estar em andamento...")
                return False
        
        # Imprimir status a cada 3 segundos
        if segundos % 3 == 0:
            print(f"Esperando download... {segundos}s passados. Arquivos incompletos: {len(incompletos)}")
        
        time.sleep(0.5)
        segundos += 0.5
    
    print(f"Timeout após {time.time() - inicio:.2f} segundos esperando download")
    return False

def ultimo_arquivo_baixado(pasta):
    """Retorna o arquivo mais recente baixado na pasta."""
    arquivos = glob.glob(os.path.join(pasta, "*"))
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getctime)

if __name__ == "__main__":
    # Certifica-se de que os argumentos são processados corretamente
    if len(sys.argv) >= 3:
        numero_instalacao = sys.argv[1]
        cpf_cnpj = sys.argv[2]
        print(f"Executando com argumentos da linha de comando: {numero_instalacao}, {cpf_cnpj}", file=sys.stderr)
    else:
        numero_instalacao = "712981"
        cpf_cnpj = "90263302000145"
        print(f"Executando com valores padrão: {numero_instalacao}, {cpf_cnpj}", file=sys.stderr)
    
    try:
        # Executar o scraper e obter o resultado
        resultado = executar_scraper_dmae(numero_instalacao, cpf_cnpj)
        
        # IMPORTANTE: Imprime APENAS o JSON sem nenhum texto adicional 
        # para o subprocess capturar corretamente - IDÊNTICO ao RGE
        print(json.dumps(resultado))
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Em caso de erro, retorna um JSON vazio mas válido
        print(json.dumps({"arquivos": [], "metricas": {"erro": str(e)}}))
        print(json.dumps({"arquivos": [], "metricas": {"erro": str(e)}}))
