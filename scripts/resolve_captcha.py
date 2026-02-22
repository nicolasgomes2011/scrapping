from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from captcha_solver import CaptchaSolver

def testar_resolver_captcha():
    # Configura o navegador
    navegador = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        # Acessa a página de teste do reCAPTCHA
        link = "https://google.com/recaptcha/api2/demo"
        navegador.get(link)
        
        # Aguarda a página carregar
        time.sleep(3)
        
        # Cria instância do solver
        solver = CaptchaSolver()
        
        # Resolve o captcha
        if solver.resolver_recaptcha(navegador):
            print("Captcha resolvido! Tentando submeter o formulário...")
            
            # Clica no botão submit
            submit_btn = navegador.find_element(By.ID, "recaptcha-demo-submit")
            submit_btn.click()
            
            time.sleep(3)
            print("Teste concluído!")
        else:
            print("Falha ao resolver o captcha.")
            
    except Exception as e:
        print(f"Erro durante o teste: {e}")
    finally:
        input("Pressione Enter para fechar o navegador...")
        navegador.quit()

if __name__ == "__main__":
    testar_resolver_captcha()