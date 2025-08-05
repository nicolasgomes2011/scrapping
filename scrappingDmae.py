#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from datetime import datetime
import time


def baixarDocumentoDMAE(matricula, cnpj):
    options = Options()
    options.headless = False  # Troque para True se quiser rodar em background
    options.add_argument('--no-sandbox')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://dmaeagvrt.procempa.com.br/gsan/exibirServicosPortalDmaeAction.do")

        if not matricula:
            print("Matricula não informada.")
        else:
            matricula_input = wait.until(
                EC.visibility_of_element_located((By.ID, "matricula"))
            )
            matricula_input.send_keys(matricula)
            
           # Clica no botão da matrícula
            submit_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn-ok"))
            )
            print("Preenchi a matricula")
            
            submit_button.click()

            print("Cliquei no primeiro submit")


            time.sleep(2)  # espera a página carregar

            # Preenche o campo CNPJ
            input_cnpj = driver.find_element(By.NAME, "cpfCnpjSolicitante")
            input_cnpj.send_keys(cnpj)
            time.sleep(2)
            # RELOCALIZA o botão para clicar depois de preencher o CNPJ
            submit_button_cnpj = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn-ok"))
            )
            submit_button_cnpj.click()
            
            print(input_cnpj)
            time.sleep(20)

            print("Cliquei no segundo submit")

            #li#serv-1 a
            
            botao_download_link = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "li#serv-1 a"))
            )
            botao_download_link.click()
            
            # CLICAR NO BOTÃO COM ALT Imprimir Fatura
            botao_imprimir = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[title()='Imprimir Fatura']/.."))
            )
            
            botao_imprimir.click()
    except Exception as e:
        print("Ocorreu um erro:", e)
        raise
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    codigo_imovel= "000935034"
    cnpj = "06210667000103"
    baixarDocumentoDMAE(codigo_imovel, cnpj)
