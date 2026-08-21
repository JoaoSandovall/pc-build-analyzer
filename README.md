# PC Build Analyzer

Sistema que recebe o upload de um orçamento de build de PC (imagem ou PDF), extrai os itens automaticamente via IA, e compara cada peça com o preço atual de mercado em múltiplas lojas — sinalizando itens acima da média e mostrando a economia potencial do orçamento.

## Índice

- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Stack tecnológica](#stack-tecnológica)
- [Como rodar localmente](#como-rodar-localmente)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Testes](#testes)
- [CI](#ci)
- [A história da migração de loja](#a-história-da-migração-de-loja)
- [Roadmap](#roadmap)

## Funcionalidades

- Cadastro e login com autenticação JWT, com rate limiting nas rotas de auth
- Upload de orçamento (imagem/PDF) direto para o S3, via URL pré-assinada
- Extração automática dos itens do orçamento por IA (nome, categoria, preço)
- Correção manual de um item extraído, caso a IA erre a categoria ou descrição
- Busca assíncrona de preço de mercado por item, em três lojas (Terabyte, Kabum, Pichau), com o melhor resultado entre elas sendo salvo
- Comparação item a item: preço do orçamento vs. preço de mercado, com veredito (`JUSTO`, `ACIMA_DA_MEDIA`, `MUITO_ACIMA`, `SEM_DADOS`)
- Histórico de orçamentos, com exclusão (cascade completo: orçamento → itens → preços de mercado)

## Arquitetura

```
[React] --> [FastAPI] --> [PostgreSQL]
   |                           ^
   v                           |
[URL pré-assinada S3] --> [Bucket S3]

[FastAPI] --(enfileira job)--> [SQS] --(consome)--> [Worker de scraping]
                                                            |
                                                    [Terabyte / Kabum / Pichau]
                                                            |
                                                            v
                                                      [PostgreSQL]
```

O upload vai direto pro S3 (o backend só gera a URL pré-assinada, não recebe o arquivo). A extração dos itens via IA acontece na rota `/budgets/process`. A partir daí, cada item pode ter seu preço de mercado buscado individualmente: a rota `/find-price` enfileira um job no SQS, e um **worker separado** (processo próprio, `worker_scraper.py`) consome a fila, faz o scraping nas três lojas e grava o melhor preço encontrado no banco.

Essa separação entre API e worker existe porque scraping é lento e sujeito a falha (timeout, bloqueio anti-bot). Se fosse síncrono dentro da própria rota da API, uma loja fora do ar travaria a experiência do usuário. Desacoplado via fila, a API responde na hora (`202 Accepted`) e o resultado fica disponível assim que o worker processar.

## Stack tecnológica

**Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, `python-jose` (JWT), `pwdlib` (hash de senha), `slowapi` (rate limiting)
**Scraping:** `cloudscraper` (contorna proteção Cloudflare/WAF), BeautifulSoup
**Frontend:** React 19, Vite, Tailwind CSS
**Banco de dados:** PostgreSQL
**AWS:** S3, SQS
**IA:** API de extração dos itens a partir do arquivo de orçamento
**Infra local:** Docker Compose (banco de dados)
**CI:** GitHub Actions (testes automatizados a cada push)
**Testes:** Pytest / `unittest`

## Como rodar localmente

### 1. Banco de dados
```bash
docker compose up -d db
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# preencha o .env com seus valores (veja a seção abaixo)

alembic upgrade head
python -m uvicorn main:app --reload
```
A API sobe em `http://127.0.0.1:8000`, com documentação interativa em `http://127.0.0.1:8000/docs`.

### 3. Worker de scraping (opcional, só necessário pra testar o `find-price`)
```bash
cd backend
python worker_scraper.py
```

### 4. Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Variáveis de ambiente

Veja `backend/.env.example` e `frontend/.env.example` para a lista completa com comentários. Resumo:

| Variável | Onde | Descrição |
|---|---|---|
| `DATABASE_URL` | backend | Conexão com o PostgreSQL |
| `SECRET_KEY` | backend | Chave de assinatura dos tokens JWT |
| `FRONTEND_URL` | backend | Origem liberada no CORS |
| `AWS_REGION`, `AWS_BUCKET_NAME` | backend | Bucket S3 dos orçamentos enviados |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | backend | Credenciais AWS (dispensável se usar IAM role) |
| `SQS_QUEUE_URL` | backend | Fila de jobs de scraping |
| `GEMINI_API_KEY` | backend | API de extração dos itens do orçamento |
| `VITE_API_URL` | frontend | URL base da API |

## Testes

```bash
cd backend
python -m pytest tests/ -v
```

> **Nota:** use sempre `python -m pytest`, não só `pytest` — sem o `-m`, o Python não adiciona a pasta atual ao `sys.path`, e os testes falham ao importar `scraper`/`schemas`. Foi um erro real que apareceu no CI (veja o histórico de commits) até ser corrigido dessa forma.

## CI

O workflow em `.github/workflows/ci.yml` roda a suíte de testes a cada push, com variáveis de ambiente de teste (mockadas — não usa banco nem credenciais reais).

## A história da migração de loja

O scraper original mirava só a Kabum. Em produção, tanto a Kabum quanto a Pichau se mostraram bem mais agressivas contra scraping do que o esperado (bloqueio por WAF/Cloudflare), então o projeto pivotou pra Terabyte primeiro, que tinha proteção mais leve — o que permitiu validar toda a arquitetura (parsing, similaridade, tratamento de item esgotado) contra um alvo real e estável.

Com o pipeline provado, o scraper foi generalizado e reforçado com `cloudscraper` para lidar com a proteção anti-bot, permitindo reativar Kabum e Pichau como fontes adicionais — hoje o worker consulta as três lojas e usa o melhor resultado entre elas.

## Roadmap

- [ ] Dockerfile do backend (empacotar API e worker)
- [ ] Atualizar `tests/test_scraper.py` para a nova assinatura do scraper genérico multi-loja (os testes atuais ainda apontam para a versão anterior, só-Terabyte, e precisam de fixtures novas)
- [ ] Validar a dead-letter queue do SQS com uma falha real (não só simulada)
- [ ] Decidir entre worker como processo de longa duração (atual) ou migrar para Lambda com trigger SQS
- [ ] Limpeza do objeto no S3 quando um orçamento é deletado (hoje o registro some do banco, mas o arquivo permanece no bucket)