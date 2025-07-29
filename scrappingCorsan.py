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

# API Keys e credenciais

anti_captcha_api="aad88f1335cb1896afac5b21659f073e"




def resolver_captcha(driver, link, site_key=None):
    
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key(anti_captcha_api)
    solver.set_website_url(link)
    solver.set_website_key(site_key)
    
    """Resolve o reCAPTCHA usando a API do AntiCaptcha"""
    if not site_key:
        site_key = extrair_site_key(driver)
        if not site_key:
            return False
    
    g_response = resolver_recaptcha_v2(driver, site_key, anti_captcha_api)
    if g_response:
        print("Captcha resolvido com sucesso!")
        return True
    else:
        print("Não foi possível resolver o captcha.")
        return False


def resolver_recaptcha_v2(driver, site_key, api_key):
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key(api_key)
    current_url = driver.current_url
    solver.set_website_url(current_url)
    solver.set_website_key(site_key)
    g_response = solver.solve_and_return_solution()
    if g_response != 0:
        print("Captcha resolvido com sucesso!")
        driver.execute_script(
            "document.getElementById('g-recaptcha-response').style.display = 'block';"
            "document.getElementById('g-recaptcha-response').value = arguments[0];",
            g_response
        )
        return g_response
    else:
        print("Não foi possível resolver o captcha. Erro:", solver.error_code)
        return None


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


def obter_mes_atual():
    
    return datetime.now().strftime("%m/%Y")

def login_rge_e_seleciona_instalacao(username, password, matricula = False, mes = obter_mes_atual()):
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
        driver.get("https://cliente.corsan.com.br")

       
        if not matricula:
            # selecionar elemento pela classe botao-entrar
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
            
            link = "https://cliente.corsan.com.br/entrar"
            site_key = driver.find_element(By.ID, "recaptcha-token").get_attribute("value")
            # site_key = driver.find_element(By.ID, "blank-frame-token").get_attribute("value")
           
            # Instancia a classe do solver 
            solver = recaptchaV2Proxyless()
            solver.set_verbose(1)
            solver.set_key(anti_captcha_api)
            solver.set_website_url(link)
            solver.set_website_key(site_key)
            
            resposta = solver.solve_and_return_solution()
            if resposta != 0:
                print(resposta)
            else:
                print("Erro ao resolver captcha:", solver.err_string)
                return
            time.sleep(1000)
            #selecionar o elemento atraves do atributo formcontrolname="cpf_cnpj"
            driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='cpf_cnpj']").send_keys(username)
            driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='matricula']").send_keys(matricula)
            
            
        
        
        # time.sleep(1000)
        
        # depois de fazer o login, espera a página carregar e acessar https://cliente.corsan.com.br/historico-faturas
        wait.until(EC.url_contains("historico-faturas"))
        
        #depois disso, preciso baixar o documento referente ao mês, nao necessariamente atual, mas um mes passado para minha função
        baixar_documento(driver, wait, mes)
            

        
    except Exception as e:
        print("Ocorreu um erro:", e)
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    username = "niltonggomes2011@gmail.com"
    password = "94488704Ngg!"
    matricula = "" #"2"
    login_rge_e_seleciona_instalacao(username, password, matricula)


