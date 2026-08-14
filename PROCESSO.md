# Processo de desenvolvimento

## Ferramentas utilizadas

- **Codex:** análise do enunciado, leitura da base existente, propostas de arquitetura, implementação assistida, testes e diagnóstico.
- **VS Code:** revisão das alterações, execução manual e commits conduzidos pelo candidato.
- **Swagger:** validação incremental do contrato HTTP.
- **pytest:** testes selecionados para riscos de domínio e regressões.
- **Docker Desktop:** reprodução do ambiente completo com OCR.
- **Tesseract:** OCR local e no container.

Acompanhei as mudanças em tempo real, executei os caminhos felizes pelo Swagger e pela interface, conferi downloads e decidi a divisão dos commits.

## Onde o agente errou ou tomou um caminho ruim

1. **Confundiu scripts de inspeção com testes reais no início.** Os arquivos `test_*.py` executavam PDFs específicos e apenas imprimiam resultados. A coleta foi restrita à pasta `tests/` e os casos relevantes foram reescritos como asserções sintéticas.
2. **Propôs inicialmente ajustar o extrator antes de confrontar o contrato literal.** A leitura do enunciado revelou campos extras, ordenação indevida e perda de `date_raw`. Os modelos e testes passaram a seguir o JSON oficial.
3. **O corpo inicial do PUT era genérico.** O Swagger sugeriu `additionalProp1`, o serviço lançou erro 500 e o teste manual revelou o problema. O request foi tipado com `CartaoPonto | Holerite`, fazendo entradas inválidas retornarem 422.
4. **A instalação do Tesseract no Windows informou português disponível, mas o arquivo tinha zero bytes.** A falha apareceu somente no OCR real. O modelo oficial foi usado localmente e o container instala `tesseract-ocr-por` de forma reproduzível.

>**O que foi reescrito ou decidido manualmente**

Utilizei IA para escrever uma parte significativa do código, mas acompanhei todo o processo e conduzi o desenvolvimento com base nos requisitos do desafio. Defini prioridades, autorizei as alterações, revisei a interface e validei manualmente os principais fluxos da aplicação: upload, processamento, revisão dos dados, edição e download das planilhas.

As implementações não foram aceitas automaticamente. Os contratos da API, os casos de teste e algumas decisões técnicas foram revisados e ajustados conforme os erros e comportamentos encontrados durante os testes.

Eu estava há algum tempo sem programar desde o encerramento do meu estágio e vários conhecimentos já não estavam tão presentes na memória. Por isso, este projeto foi desenvolvido de forma assistida por IA, mas sempre orientado pelos requisitos, pelos testes automatizados e pela minha validação manual.

Ao longo do desenvolvimento, percebi que muitos conceitos começaram a se conectar novamente. Este foi o desafio técnico mais complexo que já realizei. A IA foi especialmente importante na implementação do backend, que era a área em que eu tinha menos experiência. No frontend, principalmente com Angular, eu já possuía mais familiaridade, mas também optei pela assistência da IA para ganhar tempo e manter o foco na entrega completa da solução.

> **Três decisões com mais de uma resposta razoável**

Durante o desenvolvimento, utilizei IA para acelerar a escrita do código, mas acompanhei cada etapa e verifiquei se o resultado atendia às regras do desafio. Entre as decisões que poderiam ter sido resolvidas de outras maneiras, destaco:

Utilizar Tesseract localmente para o OCR: seria possível utilizar um serviço externo de reconhecimento de documentos, mas escolhi uma solução local para evitar custos, dependência de credenciais e envio dos documentos para terceiros.

Criar estratégias de extração específicas para cada layout: outra possibilidade seria tentar construir um extrator totalmente genérico. Optei por identificar os layouts conhecidos e aplicar regras próprias para cada um, pois isso tornou os resultados mais previsíveis e permitiu que formatos desconhecidos fossem rejeitados de maneira explícita, sem gerar dados incorretos silenciosamente.

Utilizar SQLite e processamento em segundo plano dentro da aplicação: em um ambiente de produção com maior volume, seria possível utilizar PostgreSQL e uma fila externa, como Celery ou RabbitMQ. Para o escopo do desafio, escolhi uma arquitetura mais simples, que atende ao caminho feliz e pode ser executada facilmente pelo avaliador com Docker.

Depois de observar a velocidade com que algumas partes foram implementadas, entendi que a IA pode reduzir bastante o tempo gasto escrevendo código. Ao mesmo tempo, ficou claro que ainda cabe ao desenvolvedor compreender os requisitos, avaliar as decisões, identificar resultados incorretos e assumir a responsabilidade pela solução entregue.

### OCR local com Tesseract

Um serviço de nuvem poderia oferecer melhor reconhecimento, mas exigiria segredo, custo e envio de documentos pessoais a terceiros. Tesseract permite execução local, Docker reproduzível e política de privacidade mais simples. A contrapartida é menor precisão em manuscritos.

### SQLite e BackgroundTasks

Redis, Celery ou outro sistema de filas seria mais robusto. Para o tempo do desafio e uma única instância, SQLite e `BackgroundTasks` mantêm o ciclo assíncrono simples e demonstrável. A limitação está explícita e não é apresentada como arquitetura de grande escala.

### Estratégias por layout

Um regex universal teria menos arquivos, mas misturaria exceções e dificultaria adicionar um layout durante a etapa ao vivo. Estratégias detectáveis e isoladas repetem alguma estrutura, porém protegem o contrato comum e falham explicitamente quando não reconhecem o documento.

## 2. O que quebra primeiro em produção?

O processamento no mesmo processo da API. OCR consome CPU e memória; vários uploads simultâneos aumentariam latência e um reinício perderia tarefas em andamento. A primeira evolução seria uma fila persistente com trabalhadores separados, idempotência e recuperação de tarefas interrompidas.

## 3. Onde não confio totalmente no que foi entregue?

Na precisão fora dos layouts digitais implementados, especialmente em digitalizações fracas e cartões manuscritos. Também não considero a associação por texto suficiente para todos os PDFs: alguns layouts exigiriam coordenadas, confiança por caractere e comparação visual. Por isso, layouts desconhecidos são recusados e os cortes estão documentados.
