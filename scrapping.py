#!/usr/bin/env python3
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
    
    
def login_rge_e_seleciona_instalacao(username, password):
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
    wait = WebDriverWait(driver, 20)

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
        try:
            cookie_close_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.onetrust-close-btn-handler"))
            )
            cookie_close_btn.click()
            print("Popup de cookies fechado.")
            time.sleep(1)  # Pequena pausa para sumir o popup
        except TimeoutException:
            print("Popup de cookies não apareceu ou já foi fechado.")

        # 8) Seleciona o input radio da instalação (primeira encontrada)
        radios = driver.find_elements(By.NAME, "instalacao")
        if not radios:
            print("Nenhuma instalação encontrada!")
            return

        radios[0].click()

        # 9) Espera 2 segundos para botão habilitar
        time.sleep(2)

        # 10) Clica no botão "Buscar" para avançar
        btn_buscar = driver.find_element(By.ID, "btn-buscar")
        btn_buscar.click()

        print("Instalação selecionada e botão Buscar clicado com sucesso!")
        print("URL atual:", driver.current_url)
        
        time.sleep(1)
        fechar_modal(driver, wait)
        
        print("Tentando baixar a conta")
        baixar_documento(driver, wait)

        time.sleep(3)  # Espera para ver o resultado
        fechar_modal(driver, wait)
        

    finally:
        driver.quit()

if __name__ == "__main__":
    username = "gomes.nicolas.2011@gmail.com"
    password = "94488704Ngg!"
    login_rge_e_seleciona_instalacao(username, password)


