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

# API Key do Anti-Captcha
anti_captcha_api = "aad88f1335cb1896afac5b21659f073e"

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

def resolver_captcha(driver, site_url):
    try:
        # Localiza iframe que contém o sitekey
        iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
        src = iframe.get_attribute("src")
        site_key = src.split("k=")[1].split("&")[0]

        # Usa anti-captcha
        solver = recaptchaV2Proxyless()
        solver.set_verbose(1)
        solver.set_key(anti_captcha_api)
        solver.set_website_url(site_url)
        solver.set_website_key(site_key)

        print("Resolvendo captcha...")
        g_response = solver.solve_and_return_solution()

        if g_response != 0:
            print("Captcha resolvido com sucesso!")

            # Injeta resposta no campo oculto
            driver.execute_script("""
                document.getElementById('g-recaptcha-response').style.display = 'block';
                document.getElementById('g-recaptcha-response').value = arguments[0];
                var event = new Event('change');
                document.getElementById('g-recaptcha-response').dispatchEvent(event);
            """, g_response)

            return True
        else:
            print("Erro ao resolver captcha:", solver.error_code)
            return False
    except Exception as e:
        print("Erro ao tentar resolver o captcha:", e)
        return False

def login_rge_e_seleciona_instalacao(username, password, matricula=False, mes=obter_mes_atual()):
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
        driver.get("https://cliente.corsan.com.br/entrar")
        time.sleep(5)  # Aguarda carregar reCAPTCHA

        if not matricula:
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
            if resolver_captcha(driver, driver.current_url):
                driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='cpf_cnpj']").send_keys(username)
                driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='matricula']").send_keys(matricula)

                # Aguarda botão de consultar estar habilitado
                time.sleep(1)
                try:
                    # Espera botão de login com matrícula aparecer e estar clicável
                    btn_consultar = driver.find_element(By.CLASS_NAME, "botao-consulta")
                    driver.execute_script("arguments[0].removeAttribute('disabled')", btn_consultar)

                    btn_consultar.click()
                    print("Botão 'Consultar' clicado com sucesso.")
                except TimeoutException:
                    print("Botão 'Consultar' não encontrado após resolver captcha.")
                    return

            else:
                print("Falha ao resolver captcha.")
                return

        
            paginaAtual = driver.current_url
            if "segunda-via-rapida" in paginaAtual:
                print("Entrei na pagina de segunda via, através da matricula")
                print(driver.page_source.lower())
                
                
                try:
                    botao_2via = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='EMITIR 2ª VIA']/.."))
                    )
                    botao_2via.click()
                    print("Botão 'EMITIR 2ª VIA' clicado com sucesso!")

                except TimeoutException:
                    print("Botão 'EMITIR 2ª VIA' não encontrado ou não clicável.")

    except Exception as e:
        print("Ocorreu um erro:", e)
        raise
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    username = "91.994.665/0001-13"
    password = ""
    matricula = "254434"
    login_rge_e_seleciona_instalacao(username, password, matricula)
