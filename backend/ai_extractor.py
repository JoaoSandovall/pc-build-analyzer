import os
import json
import boto3
import logging
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

class ExtractionError(RuntimeError):
    """Erro controlado de comunicação ou resposta inválida do extrator."""

def extrair_itens_orcamento_via_ia(s3_file_key: str):
    extensao = s3_file_key.split('.')[-1].lower()
    
    if not BUCKET_NAME:
        raise ExtractionError("AWS_BUCKET_NAME não está configurado")
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ExtractionError("GEMINI_API_KEY não está configurada")

    genai.configure(api_key=api_key)

    descriptor, caminho_local = tempfile.mkstemp(suffix=f".{extensao}")
    os.close(descriptor)
    
    try:
        logger.info(f"Baixando arquivo {s3_file_key} do S3...")
        s3_client.download_file(BUCKET_NAME, s3_file_key, caminho_local)
        
        mime_type = "image/jpeg"
        if extensao == "png":
            mime_type = "image/png"
        elif extensao == "pdf":
            mime_type = "application/pdf"
            
        logger.info("Lendo o arquivo localmente...")

        with open(caminho_local, "rb") as f:
            file_bytes = f.read()
            
        prompt = """
        Você é um especialista em montagem de computadores (PC Build).
        Leia o arquivo em anexo (um orçamento ou carrinho de loja de informática).
        
        Sua missão é extrair CADA peça de computador presente na lista, o seu respectivo preço (o preço unitário à vista, se houver) e TENTAR IDENTIFICAR O NOME DA LOJA que gerou o documento.
        
        Regras muito importantes:
        1. Ignore itens que NÃO são hardware (ex: frete, montagem, garantia estendida, cadeira, mesa).
        2. Categorize cada peça estritamente usando APENAS UMA destas opções:
           GPU, FONTE, GABINETE, FAN, PLACA_MAE, CPU, RAM, ARMAZENAMENTO, COOLER, OUTRO.
        3. Se não conseguir identificar a loja pelo layout ou nome no documento, retorne null no campo loja_origem.
        4. Devolva a resposta EXCLUSIVAMENTE em formato JSON. Não escreva nenhum texto antes ou depois do JSON.
        
        O formato JSON deve ser exatamente assim:
        {
          "valor_total_orcamento": 5500.00,
          "itens": [
            {
              "descricao_original": "Placa de Vídeo RTX 4060 Ti 8GB Gigabyte",
              "categoria": "GPU",
              "preco_orcamento": 2499.99,
              "loja_origem": "Kabum"
            }
          ]
        }
        """
        
        logger.info("Enviando requisição via SDK oficial do Gemini...")
        model = genai.GenerativeModel("gemini-3.6-flash")
        
        conteudo_arquivo = {
            "mime_type": mime_type,
            "data": file_bytes
        }
        
        response = model.generate_content(
            [prompt, conteudo_arquivo],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        try:
            texto_puro = response.text.strip()
            dados_extraidos = json.loads(texto_puro)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ExtractionError("A IA retornou uma resposta em formato inválido") from exc

        logger.info("Análise da IA concluída com sucesso!")
        return dados_extraidos

    except Exception as exc:
        if isinstance(exc, ExtractionError):
            raise
        logger.warning("Falha de comunicação com o provedor de IA: %s", exc)
        raise ExtractionError("Não foi possível comunicar com o provedor de IA") from exc
        
    finally:
        if os.path.exists(caminho_local):
            os.remove(caminho_local)