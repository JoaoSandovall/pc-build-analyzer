# PC Build Analyzer

Plataforma distribuída para análise automatizada de orçamentos de hardware. O sistema recebe um orçamento em imagem ou PDF, extrai os itens via IA multimodal, categoriza cada componente e compara os preços informados com o mercado através de scraping assíncrono, retornando um veredito de custo-benefício por item.

## Sumário

- [Visão geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Fluxo de dados](#fluxo-de-dados)
- [Stack tecnológica](#stack-tecnológica)
- [Destaques de engenharia](#destaques-de-engenharia)
- [Modelo de dados](#modelo-de-dados)
- [API](#api)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como rodar localmente](#como-rodar-localmente)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Testes e CI](#testes-e-ci)
- [Limitações conhecidas e próximos passos](#limitações-conhecidas-e-próximos-passos)

## Visão geral

Montar um PC costuma envolver comparar orçamentos vindos de fontes heterogêneas — prints de carrinho, PDFs de loja, listas digitadas à mão — sem um formato comum. O PC Build Analyzer resolve isso em quatro etapas:

1. **Upload direto para a nuvem.** O arquivo vai do navegador direto para um bucket S3 via *presigned URL*, sem passar pelo backend.
2. **Extração via IA multimodal.** Um modelo de visão (Google Gemini) lê o arquivo e devolve a lista de peças, preços e a loja de origem, em JSON estruturado.
3. **Validação e persistência.** A resposta da IA é validada com Pydantic antes de virar registro no PostgreSQL — nada não confiável chega ao banco sem passar por um contrato de schema.
4. **Comparação de mercado.** Para cada item, o usuário pode disparar uma busca de preço; um worker dedicado consulta múltiplas lojas em paralelo e calcula um veredito (`JUSTO`, `ACIMA_DA_MEDIA`, `MUITO_ACIMA`).

## Arquitetura

```
┌──────────┐      presigned URL       ┌────────────┐
│ Frontend │ ────────────────────────▶│   AWS S3   │
│ (React)  │                          └─────┬──────┘
└────┬─────┘                                │
     │ REST (JWT)                           │ download do arquivo
     ▼                                      ▼
┌──────────────────────────────────────────────────┐
│                    API (FastAPI)                  │
│  auth · upload-url · process · comparison · CRUD  │
└────┬───────────────────────────────────┬──────────┘
     │ extração multimodal                │ enfileira job
     ▼                                    ▼
┌──────────────┐                   ┌─────────────┐
│ Google Gemini │                  │   AWS SQS   │
└──────────────┘                   └──────┬──────┘
                                           │ consome
                                           ▼
                                 ┌───────────────────┐
                                 │  Worker (scraper)  │
                                 │ Terabyte / Kabum /  │
                                 │      Pichau         │
                                 └─────────┬──────────┘
                                           ▼
                                 ┌───────────────────┐
                                 │    PostgreSQL      │
                                 └───────────────────┘
```

A API e o worker são processos independentes (containers separados no `docker-compose`), comunicando-se apenas pela fila e pelo banco — nenhum dos dois depende do outro estar de pé para funcionar isoladamente.

## Fluxo de dados

1. `POST /budgets/upload-url` — a API valida a extensão do arquivo, cria o registro do orçamento com status `pendente` e devolve uma URL pré-assinada do S3.
2. O frontend envia o arquivo diretamente ao S3 usando essa URL.
3. `POST /budgets/process` — a API confirma que o objeto existe no S3 (`head_object`), marca o orçamento como `processando` sob *row lock* (`with_for_update`) para evitar processamento duplicado concorrente, baixa o arquivo e envia para o Gemini.
4. A resposta da IA é validada contra o schema `ExtractionResult`; falhas de validação ou de comunicação marcam o orçamento como `erro` sem derrubar a requisição.
5. `GET /budgets/{id}/comparison` — monta o payload de comparação: preço do orçamento vs. menor preço e preço médio encontrados no mercado, com o veredito calculado.
6. `POST /budgets/{id}/items/{item_id}/find-price` — não faz scraping na própria requisição; apenas publica uma mensagem na fila SQS e responde `202 Accepted` imediatamente.
7. O worker consome a fila, dispara os três scrapers em paralelo (`ThreadPoolExecutor`), grava os preços encontrados em `market_prices` e atualiza o `status_scraping` do item.
8. O frontend faz *polling* do endpoint de comparação até o item sair do estado `pendente`.

## Stack tecnológica

**Backend**
- Python 3.11, FastAPI, Pydantic v2
- SQLAlchemy 2.0 + Alembic (migrações versionadas)
- PostgreSQL
- `python-jose` (JWT) + `pwdlib` (hash de senha, Argon2)
- `slowapi` (rate limiting por rota)
- `boto3` (S3 e SQS)
- `google-generativeai` (Gemini, extração multimodal)
- `cloudscraper` + `BeautifulSoup4` (scraping)
- `pytest` (testes unitários)

**Frontend**
- React 19 + Vite
- Tailwind CSS v4

**Infraestrutura**
- AWS S3 (armazenamento de orçamentos, upload via presigned POST)
- AWS SQS (fila de jobs de scraping)
- Docker / docker-compose (API, worker e banco local)
- GitHub Actions (pipeline de testes no backend)

## Destaques de engenharia

### Desacoplamento via fila de mensagens
Scraping de e-commerce é lento e sujeito a bloqueio anti-bot — fazer isso de forma síncrona dentro da requisição do usuário levaria a timeouts constantes. A busca de preço foi desenhada como evento assíncrono: a API só publica o job na fila SQS e devolve `202 Accepted`; quem executa o trabalho pesado é um worker isolado, que pode escalar e reiniciar independentemente da API.

### Concorrência controlada no worker
Cada job dispara os três scrapers (Terabyte, Kabum, Pichau) simultaneamente via `ThreadPoolExecutor`, em vez de sequencialmente. Falha de uma loja (bloqueio anti-bot, timeout) não derruba as demais: o item só é marcado como erro se **todas** as lojas falharem na mesma execução; caso contrário, os preços das lojas que responderam são persistidos normalmente.

### Heurística de similaridade para hardware
Similaridade textual pura (interseção de tokens / menor conjunto, no estilo Jaccard) comete falsos positivos característicos de hardware — por exemplo, dar match entre uma RTX 4060 e uma RTX 4070 por compartilharem a maior parte das palavras da descrição. A função `_similaridade` corrige isso exigindo correspondência exata de todo token numérico com 3+ dígitos entre a busca e o resultado antes de considerar qualquer score; sem esse filtro, o score de similaridade textual sozinho não é suficiente para diferenciar modelos de uma mesma família.

### Extração via visão computacional em vez de OCR clássico
O desenho inicial prevẽia AWS Textract + regras de RegEx para capturar preços. O problema é que o layout de orçamentos varia por loja, por versão do site e por como o usuário exportou o arquivo — regras fixas quebram com facilidade. A extração foi migrada para um modelo multimodal (Gemini), que interpreta a estrutura da tabela visualmente e devolve JSON estrito, validado por Pydantic antes de tocar o banco. É uma troca consciente: perde-se o determinismo do OCR clássico, ganha-se tolerância a formatos não previstos.

### Parsing de preço tolerante a formatação brasileira
`_parse_preco_brl` lida com separador de milhar (`.`) e decimal (`,`) no padrão brasileiro, descarta o valor de parcelamento quando há um preço à vista relatado separadamente (`De: R$ X por: R$ Y`) e filtra ruído (preços muito abaixo do maior valor encontrado no mesmo bloco de texto, tipicamente parcelas soltas ou preços de acessórios não relacionados).

### Consistência transacional na extração
`processar_orcamento` roda sob lock de linha (`with_for_update`) e trata separadamente erro de validação da IA (`422`, orçamento marcado como `erro`) de erro inesperado (relança a exceção após marcar o orçamento como `erro`, preservando o rastro no log). Reprocessar um orçamento já `concluido` é idempotente — devolve o resultado existente em vez de rodar a IA de novo.

## Modelo de dados

| Tabela | Campos principais | Relação |
|---|---|---|
| `users` | `id`, `email` (único), `senha_hash` | 1:N com `budgets` |
| `budgets` | `id`, `user_id`, `nome_arquivo`, `s3_key` (único), `status`, `valor_total_orcamento` | 1:N com `items` |
| `items` | `id`, `budget_id`, `descricao_original`, `categoria`, `preco_orcamento`, `loja_origem`, `status_scraping` | 1:N com `market_prices` |
| `market_prices` | `id`, `item_id`, `loja`, `preco`, `url_produto`, `nome_produto_encontrado`, `coletado_em` | N:1 com `items` |

`status` de `budgets`: `pendente` → `processando` → `concluido` / `erro`.
`status_scraping` de `items`: `pendente` → `concluido` / `erro`.

Índices dedicados em `budgets.user_id`, `items.budget_id`, `market_prices.item_id` e `(market_prices.item_id, coletado_em)` sustentam as consultas mais frequentes (listagem por usuário, comparação por orçamento). Todas as alterações de schema estão versionadas em `backend/alembic/versions/`.

## API

Todas as rotas abaixo (exceto `/auth/*`) exigem `Authorization: Bearer <token>`.

| Método | Rota | Descrição | Limite |
|---|---|---|---|
| `POST` | `/auth/register` | Cria uma conta | 3/min |
| `POST` | `/auth/login` | Autentica e devolve JWT | 5/min |
| `POST` | `/budgets/upload-url` | Gera URL pré-assinada de upload no S3 | 10/h |
| `POST` | `/budgets/process` | Dispara a extração via IA para um orçamento já enviado | 10/h |
| `GET` | `/budgets` | Lista os orçamentos do usuário (paginado) | — |
| `GET` | `/budgets/{budget_id}` | Detalha um orçamento e seus itens | — |
| `DELETE` | `/budgets/{budget_id}` | Remove um orçamento e seus itens em cascata | — |
| `PATCH` | `/budgets/{budget_id}/items/{item_id}` | Corrige descrição, categoria ou preço de um item | — |
| `POST` | `/budgets/{budget_id}/items/{item_id}/find-price` | Enfileira a busca de preço de mercado do item | 20/h |
| `GET` | `/budgets/{budget_id}/comparison` | Retorna a comparação completa com veredito por item | — |

Documentação interativa (Swagger) disponível em `/docs` com a API rodando.

## Estrutura do projeto

```
backend/
├── main.py                # entrada da API, CORS, rate limiter, rotas
├── models.py               # modelos SQLAlchemy
├── schemas.py               # contratos Pydantic (entrada/saída)
├── database.py               # engine e sessão do SQLAlchemy
├── dependencies.py            # auth (JWT) e injeção de sessão de banco
├── security.py                # hash de senha e emissão de token
├── rate_limiter.py              # configuração do slowapi
├── ai_extractor.py               # integração com o Gemini
├── scraper.py                     # scrapers e heurística de similaridade
├── s3_client.py                    # presigned URL e checagem de objeto
├── sqs_client.py                    # publicação e consumo de mensagens
├── worker_scraper.py                 # processo worker (fila → scraping → banco)
├── routers/
│   ├── auth.py                        # /auth
│   └── budgets.py                      # /budgets
├── alembic/versions/                    # migrações versionadas
└── tests/                                # testes unitários + fixtures HTML

frontend/
├── src/
│   ├── pages/            # AuthScreen, Dashboard
│   ├── components/         # UploadZone, ResultsView, HistoryView, modais, UI
│   ├── hooks/                # useDashboardLogic (orquestração de estado)
│   ├── services/               # cliente da API
│   ├── contexts/                 # ToastContext
│   └── utils/                      # formatadores
```

## Como rodar localmente

### 1. Pré-requisitos
- Docker e Docker Compose
- Node.js 20+
- Conta AWS com um bucket S3 e uma fila SQS configurados
- Chave de API do Google Gemini

### 2. Banco de dados, API e worker
```bash
# configure backend/.env (veja a seção de variáveis abaixo)
docker-compose up -d
```
Isso sobe três serviços: `db` (PostgreSQL na porta `5433`), `api` (FastAPI na porta `8080`) e `worker` (consumidor da fila SQS).

### 3. Migrações do banco
```bash
docker-compose exec api alembic upgrade head
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
Configure `VITE_API_URL` (padrão `http://localhost:8000`) apontando para a API.

## Variáveis de ambiente

`backend/.env`:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | String de conexão do PostgreSQL |
| `SECRET_KEY` | Chave usada para assinar os JWTs |
| `FRONTEND_URL` | Origem permitida no CORS |
| `AWS_REGION` | Região da AWS (S3 e SQS) |
| `AWS_BUCKET_NAME` | Bucket S3 dos orçamentos enviados |
| `SQS_QUEUE_URL` | URL da fila de jobs de scraping |
| `GEMINI_API_KEY` | Chave de API do Google Gemini |

`frontend/.env`:

| Variável | Descrição |
|---|---|
| `VITE_API_URL` | URL base da API (padrão: `http://localhost:8000`) |

## Testes e CI

```bash
cd backend
pytest tests/ -v
```

Os testes cobrem o parsing de preço em formato brasileiro, a heurística de similaridade (incluindo o caso de falso positivo entre modelos de GPU distintos) e o parsing de resultados HTML a partir de uma fixture real de página de busca. O GitHub Actions (`.github/workflows/ci.yml`) roda essa suíte a cada push e pull request para `main`.

## Limitações conhecidas e próximos passos

- **Sem endpoint agregado de dashboard.** Hoje a comparação é sempre por orçamento individual; um resumo entre todos os orçamentos do usuário (total gasto, economia acumulada, distribuição por categoria) ainda não existe.
- **Sem infraestrutura como código.** Bucket S3, fila SQS e banco em produção são provisionados manualmente; não há Terraform/CDK no repositório.
- **Sem deploy contínuo.** O CI atual cobre apenas testes; não há pipeline de deploy automatizado para a API, o worker ou o frontend.
- **Dependência de disponibilidade do Gemini.** A extração fica indisponível se o provedor de IA estiver fora do ar ou alterar o formato de resposta; não há fallback para outro modelo.
- **Scraping sujeito a mudanças de layout.** As três lojas suportadas dependem da estrutura HTML atual de cada site; mudanças de layout podem exigir ajuste nos parsers.
