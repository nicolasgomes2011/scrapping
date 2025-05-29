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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_conta_cpfl(username: str, password: str, download_dir: str):
    # --- Configurações do Chrome headless e download automático de PDF ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": download_dir,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    wait = WebDriverWait(driver, 15)

    try:
        # === 1) LOGIN ===
        driver.get("https://www.cpfl.com.br/login")
        # espera os campos de login aparecerem
        wait.until(EC.presence_of_element_located((By.ID, "signInName")))
        # preenche usuário e senha
        driver.find_element(By.ID, "signInName").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        # submete o formulário
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        # aguarda redirecionamento / login concluído
        wait.until(EC.url_contains("agencia-virtual"))

        # === 2) AGÊNCIA VIRTUAL / PASSOS INICIAIS ===
        driver.get("https://www.cpfl.com.br/agencia-virtual/pagina-inicial")
        time.sleep(2)  # pequeno delay para carregar scripts

        # 2.1) Selecionar instalação (se existir)
        try:
            instal_btn = driver.find_element(By.CSS_SELECTOR, ".instalacao")
            instal_btn.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # 2.2) Fechar popup (se existir)
        try:
            fechar_popup = driver.find_element(By.CSS_SELECTOR, ".fechar-popup")
            fechar_popup.click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # 3) Clicar no botão “Ver conta completa”
        # aguarda o botão estar presente
        btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "entenda-conta")))
        btn.click()

        # 4) Aguarda download iniciar
        # (opcional: você pode monitorar a existência do arquivo na pasta)
        time.sleep(10)
        print(f"✅ Download iniciado em: {download_dir}")

    except (NoSuchElementException, TimeoutException) as e:
        print("❌ Erro ao executar o script:", e)
    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Baixa automaticamente a 'conta completa' da CPFL (PDF) em headless"
    )
    parser.add_argument("-u", "--username", required=True,
                        help="Seu usuário (e-mail ou CPF cadastrado)")
    parser.add_argument("-p", "--password", required=True,
                        help="Sua senha")
    parser.add_argument("-d", "--download-dir", default=os.getcwd(),
                        help="Pasta onde o PDF será salvo (padrão: atual)")
    args = parser.parse_args()

    os.makedirs(args.download_dir, exist_ok=True)
    download_conta_cpfl(args.username, args.password, args.download_dir)
