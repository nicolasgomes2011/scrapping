#!/usr/bin/env python3
# download_cpfl_pdf_selenium.py

import os
import time
import argparse
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_conta_cpfl(username: str, password: str, download_dir: str):
    # --- Chrome headless + download automático de PDF ---
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
        "download.default_directory": download_dir,
        "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    wait = WebDriverWait(driver, 20)

    try:
        # 1) Vai na página de login principal
        driver.get("https://www.cpfl.com.br/login")

        # 2) Aguarda (até 20s) redirect para o domínio B2C
        try:
            wait.until(EC.url_contains("b2clogin.com"))
        except TimeoutException:
            print("⚠️  Warning: não redirecionou para b2clogin.com no tempo esperado, continuando...")

        # (Opcional) fecha banner de cookies se aparecer
        try:
            btn = wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "button[aria-label*='Aceitar'], button.cookie-close, .cookie__accept"
            )))
            btn.click()
        except Exception:
            pass

        # 3) Preenche usuário e senha
        usr = wait.until(EC.element_to_be_clickable((By.ID, "signInName")))
        usr.click()
        usr.send_keys(username)

        pwd = wait.until(EC.element_to_be_clickable((By.ID, "password")))
        pwd.click()
        pwd.send_keys(password)

        # 4) Submete o formulário
        submit = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, "button[type='submit']"
        )))
        submit.click()

        # 5) Espera receive-token (mas não falha se der timeout)
        try:
            wait.until(EC.url_contains("b2c-auth/receive-token"))
        except TimeoutException:
            print("⚠️  Warning: receive-token não aconteceu a tempo, prosseguindo...")

        # 6) Navega para a Agência Virtual
        driver.get("https://www.cpfl.com.br/agencia-virtual/pagina-inicial")
        time.sleep(2)

        # 7) Seleciona instalação se aparecer
        try:
            driver.find_element(By.CSS_SELECTOR, ".instalacao").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # 8) Fecha popup se aparecer
        try:
            driver.find_element(By.CSS_SELECTOR, ".fechar-popup").click()
            time.sleep(1)
        except NoSuchElementException:
            pass

        # 9) Clica no “Ver conta completa”
        conta_btn = wait.until(EC.element_to_be_clickable(
            (By.CLASS_NAME, "entenda-conta")
        ))
        conta_btn.click()

        # 10) Aguarda o download começar
        time.sleep(10)
        print(f"✅ Download iniciado em: {download_dir}")

    except Exception as e:
        print("❌ Erro durante a execução:")
        print(f"Tipo: {type(e).__name__} — Mensagem: {e}")
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Baixa automaticamente a 'conta completa' da CPFL (PDF)"
    )
    p.add_argument("-u", "--username", required=True,
                   help="E-mail ou CPF cadastrado")
    p.add_argument("-p", "--password", required=True,
                   help="Sua senha")
    p.add_argument("-d", "--download-dir", default=os.getcwd(),
                   help="Pasta onde salvar o PDF (padrão: atual)")
    args = p.parse_args()

    os.makedirs(args.download_dir, exist_ok=True)
    download_conta_cpfl(args.username, args.password, args.download_dir)
