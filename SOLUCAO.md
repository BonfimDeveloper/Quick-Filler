# Quick Filler - Solução

## Como executar

Pré-requisito: Docker Desktop com suporte a WSL 2.

```bash
docker compose up --build
```

A aplicação fica disponível em `http://localhost:8080`. O Nginx serve o Angular e encaminha `/api` ao FastAPI. O endpoint de saúde é `GET /healthz`.

Para desenvolvimento sem Docker, execute o FastAPI em `backend/` e `npm start` em `frontend/`. O proxy do Angular aponta para `127.0.0.1:8000`.

## Arquitetura

- **Angular:** upload, acompanhamento por polling, PDF ao lado da tabela, revisão editável e downloads.
- **FastAPI:** contrato HTTP, validação, processamento em segundo plano e persistência.
- **SQLite:** estado da transcrição entre upload, revisão e download.
- **Extratores por estratégia:** cada layout conhecido é isolado, preservando um modelo comum por tipo.
- **pypdf + Tesseract:** texto embutido quando útil e OCR por página como fallback.
- **openpyxl:** XLSX; a mesma transcrição corrigida também gera CSV e JSON.

O pipeline de upload, processamento, revisão e download é compartilhado entre cartão de ponto e holerite. Apenas detecção, extração e formato tabular mudam.

## Casos suportados

- Cartão de ponto SIPON (`time-card-01`).
- Ficha financeira (`payroll-01`), com múltiplas competências por página física.
- Declaração de remuneração (`payroll-02`).
- Demonstrativo mensal (`payroll-03`).
- PDFs escaneados passam por OCR; layouts ainda não suportados terminam com erro legível, sem produzir dados vazios como sucesso.

## Planilhas de exemplo

As planilhas produzidas pelo fluxo completo estão em `exemplos-gerados/`. A pasta contém os arquivos XLSX dos quatro layouts suportados e um README que relaciona os exemplos ainda não convertidos devido ao corte de escopo documentado.

## Honestidade e validação

- Valores monetários permanecem strings no formato impresso.
- `date_raw` e `time_raw` não são substituídos pelo normalizado.
- Layout desconhecido é recusado explicitamente.
- Caracteres `?` são preservados e destacados.
- Datas inválidas não são convertidas em datas aparentemente válidas.
- Avisos são derivados, nunca armazenados no JSON.

Os testes foram escolhidos para proteger o contrato literal, a ordem dos registros, dias sem batidas, duplicidades, separação entre verbas e bases, fallback OCR, recusa de layout desconhecido, edição e estrutura das planilhas. Cobertura numérica não foi usada como objetivo.

## Segurança, privacidade e retenção

- Upload limitado a 10 MB, configurável por `MAX_UPLOAD_SIZE`.
- MIME type e assinatura `%PDF` são validados.
- Nome original não é utilizado no armazenamento; os arquivos recebem UUID.
- PDF, resultado e registro expiram após 24 horas por padrão, configurável por `RETENTION_HOURS`.
- A limpeza é oportunística: ocorre ao criar ou listar transcrições. Em produção de maior escala, seria substituída por tarefa agendada independente.
- Banco e uploads ficam no volume Docker `quick_filler_data`.
- Conteúdo, nome, CPF, salário e texto extraído não são escritos nos logs. Logs de acesso contêm método, rota técnica e status.
- Não há segredos no repositório.

## Limitações e cortes de escopo

- `time-card-02`, `time-card-03`, `time-card-04` e `payroll-04` passam pelo OCR, mas seus layouts ainda não possuem estratégia de extração.
- O cartão manuscrito é deliberadamente recusado em vez de ter números adivinhados.
- `BackgroundTasks` executa no processo da API. Um reinício durante o trabalho pode deixar um registro em `processando`; uma fila persistente seria a primeira evolução operacional.
- SQLite atende à demonstração e execução única, mas não a múltiplas réplicas concorrentes.
- A limpeza depende de tráfego na API.
- A aplicação ainda não carrega uma revisão antiga após atualizar o navegador, embora os dados permaneçam acessíveis pelo ID.

## Configuração

Consulte `.env.example`. No Docker, o Tesseract e o idioma português são instalados na imagem. No Windows, `TESSERACT_CMD` e `TESSDATA_DIR` podem apontar para a instalação local.
