import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class RgeScrapper:
    def __init__(self, url_base: str):
        self.url_base = url_base

    def obter_conteudo_pagina(self):
        """Faz a requisição HTTP e retorna o conteúdo da página."""
        try:
            resposta = requests.get(self.url_base)
            if resposta.status_code != 200:
                print(f"Erro ao acessar {self.url_base}: {resposta.status_code}")
                return None
            return resposta.content
        except Exception as e:
            print(f"Erro: {e}")
            return None

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
            resposta_doc = requests.get(url_documento)
            if resposta_doc.status_code != 200:
                print(f"Erro ao baixar o documento: {resposta_doc.status_code}")
                return False
            with open('conta_luz.pdf', 'wb') as f:
                f.write(resposta_doc.content)
            print("Documento baixado com sucesso.")
            return True
        except Exception as e:
            print(f"Erro: {e}")
            return False

    def executar(self):
        """Executa o fluxo completo de scraping e download."""
        conteudo = self.obter_conteudo_pagina()
        if conteudo:
            url_documento = self.extrair_link_conta_luz(conteudo)
            if url_documento:
                return self.baixar_documento(url_documento)
        return False


if __name__ == "__main__":
    url_inicial = "https://exemplo.com/rge"  # substitua pela URL real
    scrapper = RgeScrapper(url_inicial)
    scrapper.executar()