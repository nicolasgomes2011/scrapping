#!/usr/bin/env python3
"""
Realiza o login no site da RGE, seleciona a primeira instalação disponível e tenta baixar o documento da conta.
Parâmetros:
    username (str): Nome de usuário (e-mail) para login no site da RGE.
    password (str): Senha correspondente ao usuário.
Fluxo da função:
    1. Inicializa o navegador Chrome com opções customizadas.
    2. Acessa a página inicial da RGE.
    3. Clica no botão de login e aguarda o carregamento da página de autenticação.
    4. Preenche os campos de usuário e senha e realiza o login.
    5. Fecha eventuais modais que possam aparecer após o login.
    6. Aguarda o carregamento da página de seleção de instalações.
    7. Fecha o popup de cookies, se presente.
    8. Seleciona a primeira instalação disponível na lista.
    9. Clica no botão "Buscar" para avançar.
    10. Fecha novamente eventuais modais.
    11. Tenta baixar o documento da conta.
    12. Fecha o navegador ao final do processo.
Observações:
    - Utiliza Selenium WebDriver para automação do navegador.
    - Inclui tratamento de exceções para lidar com elementos que podem não estar presentes ou clicáveis.
    - Realiza pequenas pausas (sleep) para garantir o carregamento e fechamento de elementos dinâmicos.
    - O navegador é fechado automaticamente ao final, mesmo em caso de erro.
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

def fechar_modal(driver, wait):
    try:
        modal_close_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".modal-close-button"))
        )
        modal_close_btn.click()
        print("Modal fechado com sucesso.")
        time.sleep(1)  # Pequena pausa para garantir que o modal sumiu
    except TimeoutException:
        print("Modal não apareceu ou já foi fechado.")

def fechar_popup_cookies(driver, wait):
    try:
        cookie_close_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.onetrust-close-btn-handler"))
        )
        cookie_close_btn.click()
        print("Popup de cookies fechado.")
        time.sleep(1)  # Pequena pausa para garantir que o popup sumiu
    except TimeoutException:
        print("Popup de cookies não apareceu ou já foi fechado.")

def baixar_documento(driver, wait):
    try:
        # Espera o botão de baixar documento ficar clicável
        btn_baixar = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.entenda-conta"))
        )
        btn_baixar.click()
        print("Botão de baixar conta clicado com sucesso!")
    except TimeoutException:
        print("Botão de baixar conta não encontrado ou não clicável.")
    



def login_rge_e_seleciona_instalacao(username, password, informacoes = {}):
    options = Options()
    options.headless = False  # Troque para True para rodar sem abrir janela
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 1)

    try:
        # 1) Acessa página inicial
        driver.get("https://www.rge-rs.com.br")

        # 2) Clica no botão de login
        sign_in_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".sign-in-text a")))
        sign_in_button.click()

        # 3) Espera a página de login carregar
        wait.until(EC.visibility_of_element_located((By.ID, "signInName")))

        # 4) Preenche usuário e senha
        driver.find_element(By.ID, "signInName").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)

        # 5) Clica no botão de enviar (login)
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        
        fechar_modal(driver, wait)

        # 6) Espera a página de instalações carregar
        wait.until(EC.url_contains("area-cliente/cadastro"))
        wait.until(EC.presence_of_element_located((By.NAME, "instalacao")))

        # 7) Fecha popup de cookies se aparecer
        
        
        fechar_popup_cookies(driver, wait)

        # 8) Seleciona o input radio da instalação (primeira encontrada)
        instalacao_id = f"instalacao-{informacoes.get('instalacao')}"
        radio = driver.find_element(By.ID, instalacao_id)
        radio.click()

        # 9) Espera 2 segundos para botão habilitar
        # time.sleep(0.5)

        # 10) Clica no botão "Buscar" para avançar
        btn_buscar = driver.find_element(By.ID, "btn-buscar")
        btn_buscar.click()

        print("Instalação selecionada e botão Buscar clicado com sucesso!")
        print("URL atual:", driver.current_url)
        
        fechar_modal(driver, wait)
        
        print("Tentando baixar a conta")
        baixar_documento(driver, wait)

        # time.sleep(3)  # Espera para ver o resultado
        fechar_modal(driver, wait)
        

    finally:
        driver.quit()

if __name__ == "__main__":
    username = "gomes.nicolas.2011@gmail.com"
    password = "94488704Ngg!"
    informacoes = {
        "instalacao": 3085266087,
    }

    login_rge_e_seleciona_instalacao(username, password, informacoes)



#32.91 segundos até o download do documento

