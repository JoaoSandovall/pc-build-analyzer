# 🖥️ PC Build Analyzer

O **PC Build Analyzer** é uma plataforma distribuída que automatiza a análise de orçamentos de hardware. O sistema extrai dados de arquivos multimodais (PDFs e Imagens) via IA Generativa, categoriza os componentes e realiza web scraping assíncrono para buscar os menores preços de mercado em tempo real, gerando um dashboard de comparação de custo-benefício.

## 🚀 O Problema e a Solução
A montagem de computadores envolve a comparação exaustiva de orçamentos recebidos em diversos formatos (prints, PDFs, texto livre). O PC Build Analyzer elimina o trabalho manual:
1. O usuário faz o upload do arquivo do orçamento direto para um bucket seguro (AWS S3) via *Presigned URLs*.
2. A aplicação aciona uma LLM Multimodal (Google Gemini) para extrair a descrição, o preço e a loja de origem.
3. A IA categoriza as peças (GPU, CPU, Placa-Mãe, etc.) padronizando os dados no PostgreSQL.
4. Um Worker em background consome mensagens (AWS SQS) e faz o *scraping* em múltiplas lojas (Terabyte, Pichau, etc.), exibindo o veredito de custo-benefício (Justo, Acima da Média, Muito Acima).

## 🛠️ Stack Tecnológica
* **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
* **Frontend:** React, Vite, Tailwind CSS v4
* **Banco de Dados:** PostgreSQL
* **Mensageria & Cloud:** AWS SQS (Dead-Letter Queues), AWS S3
* **Inteligência Artificial:** Google Gemini 3.6 Flash (Vision/Multimodal)
* **Scraping:** BeautifulSoup, Cloudscraper, ThreadPoolExecutor

## 🧠 Destaques de Engenharia & Arquitetura

Durante o desenvolvimento deste MVP, vários desafios reais de engenharia foram superados:

### 1. Arquitetura Orientada a Eventos (Decoupling)
O scraping de e-commerces é inerentemente lento e instável. Fazer isso de forma síncrona na requisição do usuário causaria *timeouts*. A solução foi desacoplar a busca: a API envia uma mensagem para a fila **AWS SQS** e retorna imediatamente para o frontend. Um **Worker isolado** consome a fila e faz o trabalho pesado.

### 2. Tolerância a Falhas e Anti-Bot (WAF)
Lojas como a *Kabum* utilizam proteções severas (PerimeterX/Cloudflare). O sistema utiliza `cloudscraper` para contornar bloqueios básicos, mas também adota resiliência arquitetural: o Worker realiza o scraping das lojas simultaneamente via **Concorrência (Multithreading)**. Se uma loja bloquear ativamente o robô com um Captcha invisível, o sistema absorve a falha graciosamente, registrando 0 resultados e salvando o menor preço das outras lojas operacionais.

### 3. "Regra de Ouro" em Similaridade de Hardware
O uso de algoritmos clássicos de NLP (como Índice de Jaccard) gera "Falsos Positivos" em hardware (ex: dar match entre uma RTX 4060 e uma RTX 4070 por compartilharem muitas palavras). A heurística de busca foi refinada para exigir **correspondência exata de numerais acima de 3 dígitos**, eliminando cruzamentos incorretos de GPUs e CPUs.

### 4. OCR Clássico vs. LLM Multimodal
O escopo inicial previa AWS Textract e RegEx para capturar os preços. Contudo, percebeu-se que o *layout* de orçamentos variava infinitamente. A solução foi migrar para **Modelos de Visão Computacional (Gemini)**, que conseguem inferir a estrutura da tabela do orçamento visualmente e devolver um JSON estrito validado pelo Pydantic.

## ⚙️ Como rodar o projeto localmente

### 1. Banco de Dados e Fila
Levante o banco de dados via Docker:
```bash
docker-compose up -d