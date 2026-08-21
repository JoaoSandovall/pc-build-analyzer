import json
import logging
import os

import boto3
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

sqs_client = boto3.client("sqs", region_name=AWS_REGION)

class QueueError(RuntimeError):
    """Erro controlado de comunicação com a fila SQS."""

def _get_queue_url() -> str:
    if not SQS_QUEUE_URL:
        raise QueueError("SQS_QUEUE_URL não está configurado")
    return SQS_QUEUE_URL


def enfileirar_job_scraping(item_id: str, descricao_original: str) -> None:
    corpo = json.dumps({"item_id": item_id, "descricao_original": descricao_original})
    try:
        sqs_client.send_message(QueueUrl=_get_queue_url(), MessageBody=corpo)
    except Exception as exc:
        logger.exception("Falha ao enfileirar job de scraping para item %s", item_id)
        raise QueueError("Não foi possível enfileirar a busca de preço.") from exc


def ler_mensagens(max_mensagens: int = 5, wait_time_seconds: int = 10) -> list[dict]:

    resposta = sqs_client.receive_message(
        QueueUrl=_get_queue_url(),
        MaxNumberOfMessages=max_mensagens,
        WaitTimeSeconds=wait_time_seconds,
    )
    return resposta.get("Messages", [])


def deletar_mensagem(receipt_handle: str) -> None:
    sqs_client.delete_message(QueueUrl=_get_queue_url(), ReceiptHandle=receipt_handle)