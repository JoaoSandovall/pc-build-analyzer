import boto3
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
s3_client = boto3.client("s3", region_name=AWS_REGION)

def _get_bucket_name() -> str:
    if not BUCKET_NAME:
        raise RuntimeError("AWS_BUCKET_NAME não está configurado")
    return BUCKET_NAME

def gerar_url_presigned(nome_arquivo: str, content_type: str = "application/octet-stream", expiracao_segundos: int = 3600):
    try:
        response = s3_client.generate_presigned_post(
            Bucket=_get_bucket_name(),
            Key=nome_arquivo,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 1, 10485760]
            ],
            ExpiresIn=expiracao_segundos
        )
        return response
    except Exception:
        logger.exception("Erro ao gerar URL pré-assinada do S3")
        return None

def object_exists(s3_key: str) -> bool:
    try:
        s3_client.head_object(Bucket=_get_bucket_name(), Key=s3_key)
        return True
    
    except Exception:
        logger.warning("Objeto não encontrado ou inacessível no S3: %s", s3_key)
        return False