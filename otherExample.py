from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def fazer_login():
    # Caminho do chromedriver - ajuste se necessário
    service = Service('chromedriver')  # Assumindo chromedriver está no PATH
    driver = webdriver.Chrome(service=service)

    try:
        driver.get("https://www.cpfl.com.br/login")

        wait = WebDriverWait(driver, 15)

        # Esperar campo do usuário aparecer e preencher
        input_email = wait.until(EC.presence_of_element_located((By.ID, "signInName")))
        input_email.clear()
        input_email.send_keys("gomes.nicolas.2011@gmail.com")

        # Esperar campo da senha aparecer e preencher
        input_password = wait.until(EC.presence_of_element_located((By.ID, "password")))
        input_password.clear()
        input_password.send_keys("93810808Ngg!")

        # Submeter o formulário (pressionar Enter no campo senha)
        input_password.send_keys(Keys.RETURN)

        # Esperar a próxima página carregar (exemplo: esperar algum elemento da página pós-login)
        time.sleep(5)  # Pode substituir por espera explícita para elemento esperado após login

        print("Login efetuado com sucesso!")

        # Aqui você pode continuar a navegação para baixar o PDF, etc.

    except Exception as e:
        print("Erro durante login:", e)
    finally:
        # Se quiser manter o navegador aberto para inspeção, comente essa linha:
        driver.quit()

if __name__ == "__main__":
    fazer_login()
