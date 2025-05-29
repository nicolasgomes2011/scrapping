#!/usr/bin/env python3
# download_pdf.py

import requests
from bs4 import BeautifulSoup
import argparse
import sys
from urllib.parse import urljoin

def login_and_download_pdf(base_url, login_url, page_url, username, password, selector, output):
    session = requests.Session()

    # 1) Fazer GET na página de login para pegar cookies e, se existir, algum token CSRF
    resp = session.get(login_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Exemplo de captura de token CSRF (se necessário):
    csrf = soup.select_one('input[name=csrf_token]')
    token = csrf['value'] if csrf else None

    # 2) Enviar credenciais
    payload = {
        'signInName': username,
        'password': password,
    }
    if token:
        payload['csrf_token'] = token

    resp = session.post(login_url, data=payload)
    resp.raise_for_status()
    # [Opcional] verificar se login deu certo
    if "logout" not in resp.text.lower():
        print("⚠️  Atenção: não consegui logar. Confira usuário/senha ou seletores.", file=sys.stderr)
        sys.exit(1)

    # 3) Acessar a página onde está o botão/link do PDF
    resp = session.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    # 4) Encontrar o link ou botão que leva ao PDF
    #    selector é um CSS selector para o <a> ou <button data-url="...">
    element = soup.select_one(selector)
    if not element:
        print(f"❌ Seletor '{selector}' não encontrado na página.", file=sys.stderr)
        sys.exit(1)

    # Tentar extrair href ou atributo data-url
    pdf_href = element.get('href') or element.get('data-url')
    if not pdf_href:
        print("❌ Não encontrei atributo href ou data-url no elemento.", file=sys.stderr)
        sys.exit(1)

    # Construir URL absoluta, se necessário
    pdf_url = urljoin(base_url, pdf_href)

    # 5) Baixar o PDF
    resp = session.get(pdf_url, stream=True)
    resp.raise_for_status()
    with open(output, 'wb') as f:
        for chunk in resp.iter_content(1024):
            f.write(chunk)

    print(f"✅ PDF salvo em: {output}")

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     description='Faz login e baixa PDF de um site via terminal')
    # parser.add_argument('--base-url',   required=True,
    #                     help='URL base do site, ex: https://exemplo.com')
    # parser.add_argument('--login-url',  required=True,
    #                     help='URL do formulário de login, ex: https://exemplo.com/login')
    # parser.add_argument('--page-url',   required=True,
    #                     help='URL da página com o botão/link do PDF')
    # parser.add_argument('--username',   required=True, help='Seu usuário')
    # parser.add_argument('--password',   required=True, help='Sua senha')
    # parser.add_argument('--selector',   required=True,
    #                     help='CSS selector do link/button que aponta para o PDF, ex: "a#baixarPdf"')
    # parser.add_argument('--output',     default='download.pdf',
    #                     help='Nome do arquivo de saída (padrão: download.pdf)')
    # args = parser.parse_args()


    base_url = "https://www.cpfl.com.br/"
    login_url = "https://www.cpfl.com.br/login"
    page_url = "www.cpfl.com.br/agencia-virtual/agencia-virtual/conta-completa"
    username = "gomes.nicolas.2011@gmail.com"
    password = "93810808Ngg!"
    selector = "entenda-conta" # seletor por css que é usado para baixar o pdf
    output = "" #nao sei o que é

    login_and_download_pdf(
        base_url,
        login_url,
        page_url,
        username,
        password,
        selector,
        output
    )
