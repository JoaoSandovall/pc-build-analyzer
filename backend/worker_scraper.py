import json
import logging
import signal
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import models
from database import SessionLocal
from scraper import (
    ScrapingError, 
    buscar_preco_terabyte, 
    buscar_preco_kabum, 
    buscar_preco_pichau
)
from sqs_client import deletar_mensagem, ler_mensagens

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_rodando = True

def _parar(signum, frame):
    global _rodando
    logger.info("Sinal de parada recebido, encerrando após o job atual...")
    _rodando = False

def _processar_mensagem(mensagem: dict) -> None:
    corpo = json.loads(mensagem["Body"])
    item_id = corpo["item_id"]
    descricao_original = corpo["descricao_original"]
    
    db = SessionLocal()
    try:
        item = db.get(models.Item, uuid.UUID(item_id))
        if item is None:
            logger.warning("Item %s não existe mais, descartando job.", item_id)
            deletar_mensagem(mensagem["ReceiptHandle"])
            return

        scrapers = [buscar_preco_terabyte, buscar_preco_kabum, buscar_preco_pichau]
        resultados_encontrados = []
        falhas_totais = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            futuros = {executor.submit(scraper, descricao_original): scraper for scraper in scrapers}
            
            for futuro in as_completed(futuros):
                try:
                    resultado = futuro.result()
                    if resultado:
                        resultados_encontrados.append(resultado)
                except ScrapingError:
                    falhas_totais += 1
        if falhas_totais == len(scrapers):
            logger.warning("Todas as lojas bloquearam o acesso para o item %s. Tentaremos de novo mais tarde.", item_id)
            return 

        if not resultados_encontrados:
            item.status_scraping = models.ScrapingStatus.ERRO
            db.commit()
            logger.info("Item %s: nenhum resultado equivalente em nenhuma loja.", item_id)
        else:
            for res in resultados_encontrados:
                item.market_prices.append(
                    models.MarketPrice(
                        loja=res.loja,
                        preco=res.preco,
                        url_produto=res.url_produto,
                        nome_produto_encontrado=res.nome_produto,
                    )
                )
            item.status_scraping = models.ScrapingStatus.CONCLUIDO
            db.commit()
            logger.info("Item %s: salvos %d preços de mercado (Terabyte/Kabum/Pichau).", item_id, len(resultados_encontrados))
            
        deletar_mensagem(mensagem["ReceiptHandle"])
    finally:
        db.close()

def main() -> None:
    signal.signal(signal.SIGINT, _parar)
    signal.signal(signal.SIGTERM, _parar)
    
    logger.info("Worker Integrado (Terabyte, Kabum, Pichau) iniciado. Aguardando jobs...")
    
    while _rodando:
        try:
            mensagens = ler_mensagens(max_mensagens=5, wait_time_seconds=10)
        except Exception:
            logger.exception("Falha ao ler a fila, tentando de novo em 5s.")
            time.sleep(5)
            continue
            
        for mensagem in mensagens:
            try:
                _processar_mensagem(mensagem)
            except Exception:
                logger.exception("Erro inesperado processando mensagem, seguindo pra próxima.")
                
    logger.info("Worker encerrado.")

if __name__ == "__main__":
    sys.exit(main())