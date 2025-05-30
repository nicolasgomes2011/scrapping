import requests
from bs4 import BeautifulSoup

url = "https://www.cpfl.com.br/login"
r = requests.get(url)
soup = BeautifulSoup(r.text, 'html.parser')
print(soup.prettify()[:1000])  # imprime os primeiros 1000 chars
form = soup.find('form')
print(form)