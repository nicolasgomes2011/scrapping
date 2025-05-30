import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class RgeScrapper:
    def __init__(self, url_base: str):
        self.url_base = url_base
        self.sessao = requests.Session()  # Cria uma sessão para manter os cookies, etc.

    def obter_conteudo_pagina(self):
        """Faz a requisição HTTP e retorna o conteúdo da página."""
        try:
            resposta = self.sessao.get(self.url_base)
            if resposta.status_code != 200:
                print(f"Erro ao acessar {self.url_base}: {resposta.status_code}")
                return None
            return resposta.content
        except Exception as e:
            print(f"Erro: {e}")
            return None

    def realizar_login(self, login: str, senha: str):
        """Realiza o login no site utilizando uma requisição POST."""
        # Exemplo: suponha que a URL de login seja obtida ou seja a mesma base
        url_login = urljoin(self.url_base, "login")  # Ajuste conforme o endpoint correto

        # Dados que serão enviados no POST (use os nomes dos campos corretos!)
        dados_login = {
            "signInName": login,
            "password": senha,
            # Se houver tokens ou campos extras, adicione aqui.
        }
        
        try:
            resposta = self.sessao.post(url_login, data=dados_login)
            if resposta.status_code == 200:
                print("Login realizado com sucesso.")
                return True
            else:
                print(f"Falha no login: {resposta.status_code}")
                return False
        except Exception as e:
            print(f"Erro durante o login: {e}")
            return False

    def extrair_link_conta_luz(self, html_content: bytes):
        """Faz o parsing do HTML e retorna a URL absoluta do documento da conta de luz."""
        soup = BeautifulSoup(html_content, 'html.parser')
        link_conta = soup.find('a', text=lambda t: t and 'conta de luz' in t.lower())
        if link_conta and link_conta.get('href'):
            return urljoin(self.url_base, link_conta['href'])
        else:
            print("Link para a conta de luz não encontrado.")
            return None

    def baixar_documento(self, url_documento: str):
        """Faz o download do documento e o salva localmente."""
        try:
            resposta_doc = self.sessao.get(url_documento)
            if resposta_doc.status_code != 200:
                print(f"Erro ao baixar o documento: {resposta_doc.status_code}")
                return False
            with open('conta_luz.pdf', 'wb') as f:
                f.write(resposta_doc.content)
            print("Documento baixado com sucesso.")
            return True
        except Exception as e:
            print(f"Erro durante o download: {e}")
            return False

    def executar(self):
        """Executa o fluxo completo de scraping, incluindo o login se necessário."""
        print("Iniciando o processo de scraping...")
        # Primeiro obtenha a página inicial
        conteudo = self.obter_conteudo_pagina()
        if conteudo:
            print("Conteúdo da página obtido com sucesso.")

            # Realiza o login
            login = "gomes.nicolas.2011@gmail.com"
            senha = "993810808Ngg!"
            if self.realizar_login(login, senha):
                # Após o login, você pode acessar páginas que necessitam autenticação
                # Exemplo: obtendo novamente o conteúdo (ou acessando outra URL específica)
                conteudo = self.obter_conteudo_pagina()
                if conteudo:
                    url_documento = self.extrair_link_conta_luz(conteudo)
                    if url_documento:
                        print(f"URL do documento encontrada: {url_documento}")
                        if self.baixar_documento(url_documento):
                            print("Processo concluído com sucesso.")
                            return True
                        else:
                            print("Falha ao baixar o documento.")
                            return False
                    else:
                        print("Não foi possível extrair a URL do documento.")
                        return False
                else:
                    print("Não foi possível obter o conteúdo da página após o login.")
                    return False
            else:
                print("Login falhou.")
                return False
        else:
            print("Não foi possível obter o conteúdo da página.")
            return False


if __name__ == "__main__":
    url_inicial = "https://exemplo.com"  # Atualize com a URL real da página inicial
    scrapper = RgeScrapper(url_inicial)
    scrapper.executar()