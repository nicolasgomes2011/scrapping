from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def obter_conta_rge(cpf, senha, caminho_salvar):
    try:
        # Configurações para modo headless
        options = Options()
        options.add_argument("--headless")  # Ativa o modo headless
        options.add_argument("--no-sandbox")  # Necessário em servidores para evitar erros de permissão
        options.add_argument("--disable-dev-shm-usage")  # Evita problemas de memória em contêineres
        options.add_argument("--disable-gpu")  # Desativa a GPU, desnecessária em modo headless
        options.add_argument("--window-size=1920,1080")  # Define o tamanho da janela para layouts corretos

        # Configura o diretório de download (opcional)
        prefs = {"download.default_directory": caminho_salvar}
        options.add_experimental_option("prefs", prefs)

        # Inicia o WebDriver com as opções headless
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        
        # Acessa o site da RGE (exemplo)
        driver.get("https://www.rge-rs.com.br")
        
        # Aguarda o campo de login aparecer
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-cpf"))  # Ajuste o ID conforme o site
        )
        
        # Preenche o CPF
        campo_cpf = driver.find_element(By.ID, "login-cpf")  # Ajuste o ID real
        campo_cpf.send_keys(cpf)
        
        # Preenche a senha
        campo_senha = driver.find_element(By.ID, "login-senha")  # Ajuste o ID real
        campo_senha.send_keys(senha)
        
        # Clica no botão de login
        botao_login = driver.find_element(By.ID, "botao-login")  # Ajuste o ID real
        botao_login.click()
        
        # Aguarda a página de contas carregar
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Segunda Via de Conta"))  # Exemplo
        )
        
        # Navega até a seção de contas
        driver.find_element(By.LINK_TEXT, "Segunda Via de Conta").click()
        
        # Aguarda o botão de download
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "download-conta"))  # Exemplo
        )
        
        # Clica para baixar o PDF
        driver.find_element(By.ID, "download-conta").click()
        
        # Aguarda o download (ajuste o tempo ou use uma verificação mais robusta)
        time.sleep(5)
        
        print(f"Conta baixada com sucesso para o cliente com CPF: {cpf}")
        
    except Exception as e:
        print(f"Erro ao processar o CPF {cpf}: {str(e)}")
        
    finally:
        # Fecha o navegador
        driver.quit()

# Exemplo de uso
cpf_cliente = "gomes.nicolas.2011@gmail.com"  # Substitua pelos dados reais
senha_cliente = "94488704Ngg!"       # Substitua pelos dados reais
caminho_salvar = "/caminho/para/salvar"  # Ajuste o caminho no servidor

obter_conta_rge(cpf_cliente, senha_cliente, caminho_salvar)