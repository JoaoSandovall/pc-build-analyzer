import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from bs4 import BeautifulSoup
import cloudscraper

def _limpar_descricao_para_busca(descricao: str) -> str:
    texto = re.sub(r'[,-/|()]', ' ', descricao)
    
    texto = re.sub(r'\b(preto|branco|white|black|box|oem|edition)\b', '', texto, flags=re.IGNORECASE)
    
    texto = re.sub(r'\b[A-Za-z0-9]{10,}\b', '', texto)
    
    palavras = texto.split()
    query_limpa = ' '.join(palavras[:7]) 
    
    return query_limpa

logger = logging.getLogger(__name__)

scraper_client = cloudscraper.create_scraper(
    browser={
        'browser': 'firefox',
        'platform': 'windows',
        'desktop': True
    }
)

scraper_client.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
})

REQUEST_TIMEOUT = (5, 20)
SIMILARIDADE_MINIMA = 0.40

STOPWORDS = {
    "de", "da", "do", "com", "para", "e", "a", "o", "novo", "nova",
    "original", "gamer", "rgb", "placa", "video", "vídeo"
}
TERMOS_INDISPONIVEL = {"esgotado", "indisponível", "indisponivel", "avise-me", "sem estoque"}

class ScrapingError(RuntimeError):
    """Erro controlado de comunicação."""

@dataclass
class ScrapedPrice:
    nome_produto: str
    preco: Decimal
    url_produto: str
    loja: str

def _parse_preco_brl(texto: str) -> Decimal | None:
    # 1. Tenta remover parcelas via RegEx (melhorado para aceitar espaços antes do X)
    texto_limpo = re.sub(r"\d{1,2}\s*[xX].*?R\$?\s*[\d.,]+", "", texto, flags=re.IGNORECASE)
    
    matches = re.findall(r"R\$\s*([\d.,]+)", texto_limpo, flags=re.IGNORECASE)
    if not matches:
        return None
        
    precos = []
    for m in matches:
        m = m.strip(".,")
        
        if re.search(r",\d{2}$", m):
            num_str = m.replace(".", "").replace(",", ".")
        elif re.search(r"\.\d{2}$", m):
            num_str = m.replace(",", "")
        else:
            num_str = m.replace(".", "").replace(",", "")
            
        try:
            val = Decimal(num_str)
            if val > Decimal("10.00"):
                precos.append(val)
        except InvalidOperation:
            continue
            
    if not precos:
        return None

    maior_preco = max(precos)
    precos_validos = [p for p in precos if p >= maior_preco * Decimal("0.3")]
    
    if not precos_validos:
        return None

    return min(precos_validos)

def _tokenizar(texto: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", texto.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}

def _similaridade(query: str, resultado: str) -> float:
    tokens_q = _tokenizar(query)
    tokens_r = _tokenizar(resultado)
    if not tokens_q or not tokens_r:
        return 0.0
        
    numeros_query = {t for t in tokens_q if t.isdigit() and len(t) >= 3}
    numeros_resultado = {t for t in tokens_r if t.isdigit() and len(t) >= 3}
    
    if numeros_query and not numeros_query.issubset(numeros_resultado):
        return 0.0
        
    intersecao = tokens_q & tokens_r
    menor_conjunto = min(len(tokens_q), len(tokens_r))
    return len(intersecao) / menor_conjunto

def _buscar_html(url: str) -> str:
    try:
        resposta = scraper_client.get(url, timeout=REQUEST_TIMEOUT)
        resposta.raise_for_status()
        return resposta.text
    except Exception as exc:
        logger.warning(f"Bloqueio anti-bot ou timeout na URL {url}: {exc}")
        raise ScrapingError(f"Falha ao acessar: {url}") from exc

def _parse_resultados(html: str, base_url: str, nome_loja: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    links_produto = soup.find_all("a", href=True)
    
    resultados = []
    vistos = set()
    
    ignorar_urls = {"/login", "/carrinho", "/categoria", "/departamento", "/institucional", "javascript:", "/sac", "/contato"}
    
    for link in links_produto:
        href = link["href"]
        url_lower = href.lower()
        
        if any(ignorar in url_lower for ignorar in ignorar_urls):
            continue
            
        nome = link.get_text(" ", strip=True)
        if not nome or len(nome) < 15:
            continue
            
        if href in vistos:
            continue
        vistos.add(href)
        
        pai = link.parent
        for _ in range(4):
            if pai is None: break
            texto_pai = pai.get_text(" ", strip=True)
            if len(texto_pai) <= 800 and "R$" in texto_pai:
                if not any(termo in texto_pai.lower() for termo in TERMOS_INDISPONIVEL):
                    preco = _parse_preco_brl(texto_pai)
                    if preco:
                        url_final = href if href.startswith("http") else f"{base_url}{href}"
                        resultados.append({"nome": nome, "preco": preco, "url": url_final, "loja": nome_loja})
                break
            pai = pai.parent
            
    return resultados

def buscar_preco_terabyte(descricao_item: str) -> ScrapedPrice | None:
    query = _limpar_descricao_para_busca(descricao_item)
    url = f"https://www.terabyteshop.com.br/busca?str={quote(query)}"
    html = _buscar_html(url)
    resultados = _parse_resultados(html, "https://www.terabyteshop.com.br", "Terabyte")
    logger.info(f"[Terabyte] {len(resultados)} produtos encontrados para '{query}'.")
    return _selecionar_melhor_resultado(descricao_item, resultados)

def buscar_preco_kabum(descricao_item: str) -> ScrapedPrice | None:
    query = _limpar_descricao_para_busca(descricao_item)
    url = f"https://www.kabum.com.br/busca/{quote(query)}"
    html = _buscar_html(url)
    resultados = _parse_resultados(html, "https://www.kabum.com.br", "Kabum")
    logger.info(f"[Kabum] {len(resultados)} produtos encontrados para '{query}'.")
    return _selecionar_melhor_resultado(descricao_item, resultados)

def buscar_preco_pichau(descricao_item: str) -> ScrapedPrice | None:
    query = _limpar_descricao_para_busca(descricao_item)
    url = f"https://www.pichau.com.br/search?q={quote(query)}"
    html = _buscar_html(url)
    resultados = _parse_resultados(html, "https://www.pichau.com.br", "Pichau")
    logger.info(f"[Pichau] {len(resultados)} produtos encontrados para '{query}'.")
    return _selecionar_melhor_resultado(descricao_item, resultados)

def _selecionar_melhor_resultado(query: str, resultados: list[dict]) -> ScrapedPrice | None:
    if not resultados:
        return None
        
    melhor = max(resultados, key=lambda r: _similaridade(query, r["nome"]))
    score = _similaridade(query, melhor["nome"])
    
    if score < SIMILARIDADE_MINIMA:
        return None
        
    return ScrapedPrice(
        nome_produto=melhor["nome"],
        preco=melhor["preco"],
        url_produto=melhor["url"],
        loja=melhor["loja"]
    )