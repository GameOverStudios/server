import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_links(url):
    links = set()
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)  # Converte URLs relativas em absolutas
            if urlparse(full_url).netloc == urlparse(url).netloc:  # Verifica se está no mesmo subdomínio
                links.add(full_url)
                
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
    
    return links

def crawl_site(start_url):
    visited = set()
    links_to_visit = {start_url}
    
    while links_to_visit:
        url = links_to_visit.pop()
        if url not in visited:
            print(f"Acessando: {url}")
            visited.add(url)
            new_links = get_links(url)
            links_to_visit.update(new_links - visited)  # Adiciona novos links não visitados

    return visited

if __name__ == "__main__":
    start_url = "https://hexdocs.pm/phoenix/"
    all_links = crawl_site(start_url)
    
    print("\nLinks encontrados:")
    for link in all_links:
        print(link)
