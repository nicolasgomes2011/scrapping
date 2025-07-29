#!/usr/bin/env python3
"""
Automatiza o login no site da RGE, seleção de instalação e download do documento da conta.
"""
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

DEFAULT_WAIT = 10

def fechar_elemento(driver, by, selector, wait, descricao):
    try:
        btn = wait.until(EC.element_to_be_clickable((by, selector)))
        btn.click()
        logging.info(f"{descricao} fechado com sucesso.")
        time.sleep(1)
    except TimeoutException:
        logging.info(f"{descricao} não apareceu ou já foi fechado.")

def baixar_documento(driver, wait):
    try:
        btn_baixar = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.entenda-conta"))
        )
        btn_baixar.click()
        logging.info("Botão de baixar conta clicado com sucesso!")
    except TimeoutException:
        logging.warning("Botão de baixar conta não encontrado ou não clicável.")

def login_rge_e_seleciona_instalacao(username, password, informacoes=None, wait_time=DEFAULT_WAIT):
    if informacoes is None:
        informacoes = {}

    import time
    start_time = time.time()  # Inicia a contagem

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, wait_time)

    try:
        driver.get("https://www.rge-rs.com.br")

        # Login
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".sign-in-text a"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "signInName")))
        driver.find_element(By.ID, "signInName").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        fechar_elemento(driver, By.CSS_SELECTOR, ".modal-close-button", wait, "Modal")

        # Seleção de instalação
        wait.until(EC.url_contains("area-cliente/cadastro"))
        wait.until(EC.presence_of_element_located((By.NAME, "instalacao")))
        fechar_elemento(driver, By.CSS_SELECTOR, "button.onetrust-close-btn-handler", wait, "Popup de cookies")

        instalacao_id = f"instalacao-{informacoes.get('instalacao')}"
        try:
            radio = driver.find_element(By.ID, instalacao_id)
            radio.click()
        except NoSuchElementException:
            logging.error(f"Instalação com ID {instalacao_id} não encontrada.")
            return

        btn_buscar = driver.find_element(By.ID, "btn-buscar")
        btn_buscar.click()
        logging.info("Instalação selecionada e botão Buscar clicado com sucesso!")
        logging.info(f"URL atual: {driver.current_url}")

        fechar_elemento(driver, By.CSS_SELECTOR, ".modal-close-button", wait, "Modal pós-busca")
        logging.info("Tentando baixar a conta")
        baixar_documento(driver, wait)

        # Calcula e exibe o tempo decorrido até o acionamento do download
        elapsed_time = time.time() - start_time
        logging.info(f"Tempo total até o download do PDF: {elapsed_time:.2f} segundos")

        fechar_elemento(driver, By.CSS_SELECTOR, ".modal-close-button", wait, "Modal final")

    except (TimeoutException, WebDriverException) as e:
        logging.error(f"Erro durante o processo: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    username = "gomes.nicolas.2011@gmail.com"
    password = "94488704Ngg!"
    informacoes = {
        "instalacao": 3085266087,
    }
    login_rge_e_seleciona_instalacao(username, password, informacoes)
