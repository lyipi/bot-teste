import requests
from bs4 import BeautifulSoup


url = "https://www.google.com/search?q=python+programming"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup.prettify())