# Planilhas geradas

Estes arquivos foram produzidos pelo fluxo completo da aplicação: upload do PDF, processamento da transcrição e download em XLSX.

## Arquivos disponíveis

- `payroll-01.xlsx`
- `payroll-02.xlsx`
- `payroll-03.xlsx`
- `time-card-01.xlsx`

## Arquivos sem planilha

`payroll-04`, `time-card-02`, `time-card-03` e `time-card-04` passam pelo OCR, mas seus layouts ainda não possuem estratégia de extração. A aplicação encerra esses casos com uma mensagem de erro legível e não gera planilhas vazias ou dados estimados.

Essa limitação também está registrada em `SOLUCAO.md`.
