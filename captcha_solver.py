from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from anti_captcha_credencials import CHAVE_DA_API

class CaptchaSolver:
    def __init__(self, api_key=CHAVE_DA_API):
        self.api_key = api_key
    
    def extrair_site_key(self, driver):
        """Extrai a site key do reCAPTCHA da página atual"""
        try:
            captcha_element = driver.find_element(By.CSS_SELECTOR, ".g-recaptcha")
            site_key = captcha_element.get_attribute("data-sitekey")
            print(f"Site key encontrada: {site_key}")
            return site_key
        except Exception as e:
            print(f"Erro ao extrair site key: {e}")
            return None
    
    def resolver_recaptcha(self, driver, site_key=None):
        """Resolve o reCAPTCHA usando a API do AntiCaptcha"""
        if not site_key:
            site_key = self.extrair_site_key(driver)
            if not site_key:
                return False
        
        solver = recaptchaV2Proxyless()
        solver.set_verbose(1)
        solver.set_key(self.api_key)
        solver.set_website_url(driver.current_url)
        solver.set_website_key(site_key)
        
        print("Resolvendo captcha...")
        g_response = solver.solve_and_return_solution()
        
        if g_response != 0:
            print("Captcha resolvido com sucesso!")
            # Injeta a solução no campo g-recaptcha-response
            driver.execute_script(
                "document.getElementById('g-recaptcha-response').style.display = 'block';"
                "document.getElementById('g-recaptcha-response').value = arguments[0];",
                g_response
            )
            # Dispara evento para notificar o formulário
            driver.execute_script(
                "if(window.grecaptcha) { window.grecaptcha.getResponse = function() { return arguments[0]; }; }",
                g_response
            )
            return True
        else:
            print(f"Não foi possível resolver o captcha. Erro: {solver.error_code}")
            return False