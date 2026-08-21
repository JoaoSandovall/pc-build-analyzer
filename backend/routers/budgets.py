from decimal import ROUND_HALF_UP, Decimal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

import models
from ai_extractor import ExtractionError, extrair_itens_orcamento_via_ia
from dependencies import get_current_user, get_db
from rate_limiter import limiter
from s3_client import gerar_url_presigned, object_exists
from sqs_client import QueueError, enfileirar_job_scraping
from schemas import (
    ComparisonItem,
    ComparisonResponse,
    ExtractionResult,
    ItemUpdate,
    MarketPriceOut,
    ProcessRequest,
    UploadRequest,
    VereditoPreco,
)

router = APIRouter(prefix="/budgets", tags=["Orçamentos e IA"])

CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "pdf": "application/pdf",
}

def serialize_budget(budget: models.Budget) -> dict:
    return {
        "budget_id": str(budget.id),
        "status": budget.status.value,
        "valor_total_orcamento": str(budget.valor_total_orcamento or Decimal("0")),
        "itens": [
            {
                "id": str(item.id),
                "descricao_original": item.descricao_original,
                "categoria": item.categoria.name if item.categoria else "OUTRO",
                "preco_orcamento": str(item.preco_orcamento),
                "loja_origem": item.loja_origem, # NOVO CAMPO: Retornando loja origem
            }
            for item in budget.items
        ],
    }

def serialize_budget_summary(budget: models.Budget) -> dict:
    return {
        "budget_id": str(budget.id),
        "nome_arquivo": budget.nome_arquivo,
        "status": budget.status.value,
        "valor_total_orcamento": str(budget.valor_total_orcamento or Decimal("0")),
        "criado_em": budget.criado_em.isoformat() if budget.criado_em else None,
    }

@router.post("/upload-url")
@limiter.limit("10/hour")
def solicitar_url_upload(
    request: Request,
    payload: UploadRequest,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    if "." not in payload.nome_arquivo:
        raise HTTPException(status_code=400, detail="O arquivo precisa ter uma extensão válida.")
    
    extensao = payload.nome_arquivo.rsplit(".", 1)[-1].lower()
    
    if extensao not in CONTENT_TYPES:
        permitidos = ", ".join(sorted(CONTENT_TYPES))
        raise HTTPException(status_code=400, detail=f"Arquivo não suportado. Envie apenas: {permitidos}")
        
    s3_key = f"orcamentos/{usuario_atual.id}/{uuid.uuid4()}.{extensao}"
    aws_post_data = gerar_url_presigned(s3_key, content_type=CONTENT_TYPES[extensao])
    
    if not aws_post_data:
        raise HTTPException(status_code=503, detail="Falha ao preparar o armazenamento do arquivo.")
        
    novo_orcamento = models.Budget(
        user_id=usuario_atual.id,
        nome_arquivo=payload.nome_arquivo,
        s3_key=s3_key,
        status=models.BudgetStatus.PENDENTE,
    )
    db.add(novo_orcamento)
    db.commit()
    db.refresh(novo_orcamento)
        
    return {
        "budget_id": str(novo_orcamento.id),
        "url_upload": aws_post_data["url"],
        "s3_fields": aws_post_data["fields"],
    }

@router.post("/process")
@limiter.limit("10/hour")
def processar_orcamento(
    request: Request,
    payload: ProcessRequest,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    orcamento = (
        db.query(models.Budget)
        .filter(models.Budget.id == payload.budget_id, models.Budget.user_id == usuario_atual.id)
        .with_for_update()
        .first()
    )
    
    if not orcamento:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
    if orcamento.status == models.BudgetStatus.CONCLUIDO:
        return serialize_budget(orcamento)
    if orcamento.status == models.BudgetStatus.PROCESSANDO:
        raise HTTPException(status_code=409, detail="Este orçamento já está sendo processado.")
    if not object_exists(orcamento.s3_key):
        raise HTTPException(status_code=409, detail="O upload ainda não foi encontrado no armazenamento.")

    orcamento.status = models.BudgetStatus.PROCESSANDO
    db.commit()
    
    try:
        extraction = ExtractionResult.model_validate(
            extrair_itens_orcamento_via_ia(orcamento.s3_key)
        )
        orcamento = db.get(models.Budget, payload.budget_id)
        
        total = sum((item.preco_orcamento for item in extraction.itens), Decimal("0"))
        orcamento.valor_total_orcamento = total
        orcamento.items.clear()
        
        for item in extraction.itens:
            orcamento.items.append(
                models.Item(
                    descricao_original=item.descricao_original,
                    categoria=models.ItemCategoria[item.categoria.value],
                    preco_orcamento=item.preco_orcamento,
                    loja_origem=item.loja_origem
                )
            )
            
        orcamento.status = models.BudgetStatus.CONCLUIDO
        db.commit()
        db.refresh(orcamento)
        return serialize_budget(orcamento)
        
    except (ExtractionError, ValidationError) as exc:
        db.rollback()
        failed_budget = db.get(models.Budget, payload.budget_id)
        failed_budget.status = models.BudgetStatus.ERRO
        db.commit()
        raise HTTPException(
            status_code=422,
            detail="Não foi possível validar a extração do orçamento.",
        ) from exc
    except Exception:
        db.rollback()
        failed_budget = db.get(models.Budget, payload.budget_id)
        failed_budget.status = models.BudgetStatus.ERRO
        db.commit()
        raise

@router.get("")
def listar_orcamentos(
    skip: int = Query(0, ge=0, description="Pular N orçamentos (Paginação)"),
    limit: int = Query(15, ge=1, le=50, description="Limite por página"),
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    budgets = (
        db.query(models.Budget)
        .filter(models.Budget.user_id == usuario_atual.id)
        .order_by(models.Budget.criado_em.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [serialize_budget_summary(budget) for budget in budgets]

@router.get("/{budget_id}")
def detalhar_orcamento(
    budget_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    budget = (
        db.query(models.Budget)
        .filter(models.Budget.id == budget_id, models.Budget.user_id == usuario_atual.id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
    return serialize_budget(budget)

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_orcamento(
    budget_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    budget = (
        db.query(models.Budget)
        .filter(models.Budget.id == budget_id, models.Budget.user_id == usuario_atual.id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
    
    db.delete(budget)
    db.commit()
    return None

@router.patch("/{budget_id}/items/{item_id}")
def corrigir_item(
    budget_id: uuid.UUID,
    item_id: uuid.UUID,
    update: ItemUpdate,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    budget = (
        db.query(models.Budget)
        .filter(models.Budget.id == budget_id, models.Budget.user_id == usuario_atual.id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
        
    item = db.query(models.Item).filter(
        models.Item.id == item_id, models.Item.budget_id == budget.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
        
    changes = update.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Informe pelo menos um campo para corrigir.")
        
    if "categoria" in changes:
        item.categoria = models.ItemCategoria[changes.pop("categoria").value]
        
    for field, value in changes.items():
        setattr(item, field, value)
        
    budget.valor_total_orcamento = sum(
        (current.preco_orcamento for current in budget.items), Decimal("0")
    )
    
    db.commit()
    db.refresh(budget)
    return serialize_budget(budget)

def _get_item_do_usuario(
    db: Session, budget_id: uuid.UUID, item_id: uuid.UUID, usuario_atual: models.User
) -> models.Item:
    item = (
        db.query(models.Item)
        .join(models.Budget)
        .filter(
            models.Item.id == item_id,
            models.Item.budget_id == budget_id,
            models.Budget.user_id == usuario_atual.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")
    return item

@router.post("/{budget_id}/items/{item_id}/find-price", status_code=202)
@limiter.limit("20/hour")
def buscar_preco_de_mercado(
    request: Request,
    budget_id: uuid.UUID,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    item = _get_item_do_usuario(db, budget_id, item_id, usuario_atual)
    try:
        enfileirar_job_scraping(str(item.id), item.descricao_original)
    except QueueError as exc:
        raise HTTPException(
            status_code=502, detail="Não foi possível enfileirar a busca de preço no momento."
        ) from exc
        
    return {"enfileirado": True, "mensagem": "Busca de preço enfileirada."}

def _calcular_veredito(preco_orcamento: Decimal, preco_medio_mercado: Decimal | None) -> VereditoPreco:
    if preco_medio_mercado is None or preco_medio_mercado == 0:
        return VereditoPreco.SEM_DADOS
    razao = preco_orcamento / preco_medio_mercado
    if razao <= Decimal("1.05"):
        return VereditoPreco.JUSTO
    if razao <= Decimal("1.20"):
        return VereditoPreco.ACIMA_DA_MEDIA
    return VereditoPreco.MUITO_ACIMA

@router.get("/{budget_id}/comparison", response_model=ComparisonResponse)
def comparar_orcamento(
    budget_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: models.User = Depends(get_current_user),
):
    budget = (
        db.query(models.Budget)
        .filter(models.Budget.id == budget_id, models.Budget.user_id == usuario_atual.id)
        .first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")
        
    itens_comparados = []
    economia_potencial = Decimal("0")
    
    for item in budget.items:
        precos = [mp.preco for mp in item.market_prices]
        menor_preco = min(precos) if precos else None
        
        preco_medio = (
            (sum(precos, Decimal("0")) / len(precos)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if precos
            else None
        )
        
        veredito = _calcular_veredito(item.preco_orcamento, preco_medio)
        
        if menor_preco is not None and item.preco_orcamento > menor_preco:
            economia_potencial += item.preco_orcamento - menor_preco
            
        itens_comparados.append(
            ComparisonItem(
                item_id=str(item.id),
                descricao_original=item.descricao_original,
                categoria=item.categoria.value if item.categoria else "Outro",
                preco_orcamento=item.preco_orcamento,
                loja_origem=item.loja_origem,
                status_scraping=item.status_scraping.value,
                menor_preco_mercado=menor_preco,
                preco_medio_mercado=preco_medio,
                veredito=veredito,
                precos_mercado=[
                    MarketPriceOut(
                        loja=mp.loja,
                        preco=mp.preco,
                        url_produto=mp.url_produto,
                        nome_produto_encontrado=mp.nome_produto_encontrado,
                        coletado_em=mp.coletado_em.isoformat() if mp.coletado_em else "",
                    )
                    for mp in item.market_prices
                ],
            )
        )
        
    return ComparisonResponse(
        budget_id=str(budget.id),
        valor_total_orcamento=budget.valor_total_orcamento or Decimal("0"),
        economia_potencial=economia_potencial,
        itens=itens_comparados,
    )