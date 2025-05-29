#!/usr/bin/env python3
# download_cpfl_pdf_selenium.py

import os
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def download_conta_cpfl(username: str, password: str, download_dir: str):
    # --- Configurações do Chrome em modo headless para download automático de PDF ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": download_dir,
        # força abrir PDF com leitor interno (e disparar download)
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", chrome_prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        # 1) Acessar a página inicial
        driver.get("https://www.cpfl.com.br/agencia-virtual/pagina-inicial")
        time.sleep(2)

        # 2) Selecionar instalação (se solicitado)
        try:
            # EXEMPLO de seletor: adapte para o elemento real na página
            inst = driver.find_element(By.CSS_SELECTOR, ".instalacao")  
            inst.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # 3) Fechar popup (se aparecer)
        try:
            # EXEMPLO de seletor de botão de fechar popup
            fechar = driver.find_element(By.CSS_SELECTOR, ".fechar-popup")  
            fechar.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # 4) Navegar para o formulário de login
        driver.find_element(By.LINK_TEXT, "Entrar").click()
        time.sleep(2)

        # 5) Preencher credenciais e submeter
        driver.find_element(By.NAME, "signInName").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(5)

        # 6) Clicar no botão “Ver conta completa” (classe entenda-conta)
        btn = driver.find_element(By.CLASS_NAME, "entenda-conta")
        btn.click()

        # Aguarda o download terminar (dependendo do tamanho, ajuste o tempo)
        time.sleep(10)

        print(f"✅ Download iniciado em: {download_dir}")

    except (NoSuchElementException, TimeoutException) as e:
        print("❌ Ocorreu um erro ao navegar/baixar:", e)
    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Baixa automaticamente a 'conta completa' da CPFL (PDF) em modo headless"
    )
    parser.add_argument(
        "--username", "-u", required=True,
        help="Seu usuário (e-mail ou CPF cadastrado na Agência Virtual)"
    )
    parser.add_argument(
        "--password", "-p", required=True,
        help="Sua senha"
    )
    parser.add_argument(
        "--download-dir", "-d", default=os.getcwd(),
        help="Pasta onde o PDF será salvo (padrão: diretório atual)"
    )
    args = parser.parse_args()

    # Garante que a pasta exista
    os.makedirs(args.download_dir, exist_ok=True)

    download_conta_cpfl(args.username, args.password, args.download_dir)
