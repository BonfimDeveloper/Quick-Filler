import re

from app.models.holerite import BaseValue, Field, Holerite, Page


MESES = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}


TIPOS_FOLHA = [
    "Folha Normal",
    "Adiantamento - PLR",
    "13 Salario",
]


BASES = [
    "BASEDECALCULODOINSS",
    "BASEDECALCULODOIRF",
    "BASEDECALCULODOFGTS",
    "VALORDOFGTS",
    "SALARIOLIQUIDONOMES",
    "VALORDOIRFARECOLHER",
]


def extrair_competencia(
    linha: str,
) -> tuple[int, int]:
    """
    Extrai mês e ano da linha de competência.

    Exemplos:

        Mês: abr-17
        Mês: jan-18 512 INSS 13o. Sal 0 347,46

    Retorna:

        (4, 2017)
        (1, 2018)
    """

    resultado = re.search(
        r"M\S*s:\s*([a-z]{3})-(\d{2})",
        linha,
        flags=re.IGNORECASE,
    )

    if not resultado:
        raise ValueError(
            f"Não foi possível identificar a competência: {linha}"
        )

    mes_texto = resultado.group(1).lower()
    ano_curto = int(resultado.group(2))

    mes = MESES.get(mes_texto)

    if mes is None:
        raise ValueError(
            f"Mês não reconhecido: {mes_texto}"
        )

    ano = 2000 + ano_curto

    return mes, ano


def extrair_tipo_folha(
    linhas: list[str],
    indice_competencia: int,
) -> tuple[str, int]:
    """
    Procura o tipo da folha nas linhas imediatamente
    anteriores à competência.

    Exemplos:

        Folha Normal
        Mês: abr-17

        Adiantamento - PLR
        Mês: out-17

        13 Salario
        Mês: dez-17
    """

    inicio_busca = max(
        0,
        indice_competencia - 3,
    )

    for indice in range(
        indice_competencia - 1,
        inicio_busca - 1,
        -1,
    ):
        linha = linhas[indice]

        for tipo in TIPOS_FOLHA:
            if tipo.lower() in linha.lower():
                return tipo, indice

    return (
        "Não identificado",
        indice_competencia,
    )


def localizar_competencias(
    linhas: list[str],
) -> list[int]:
    """
    Localiza todas as linhas que possuem competência.

    Exemplo:

        Mês: abr-17
        Mês: mai-17
        Mês: jun-17
    """

    indices = []

    padrao = re.compile(
        r"M\S*s:\s*[a-z]{3}-\d{2}",
        flags=re.IGNORECASE,
    )

    for indice, linha in enumerate(linhas):
        if padrao.search(linha):
            indices.append(indice)

    return indices


def extrair_blocos(
    texto: str,
) -> list[dict]:
    """
    Divide o texto completo em blocos de holerite.

    Cada ocorrência de competência representa
    um novo bloco lógico.
    """

    linhas = texto.splitlines()

    competencias = localizar_competencias(
        linhas
    )

    blocos = []

    for posicao, indice_competencia in enumerate(
        competencias
    ):
        linha_competencia = linhas[
            indice_competencia
        ]

        mes, ano = extrair_competencia(
            linha_competencia
        )

        tipo_folha, indice_tipo = (
            extrair_tipo_folha(
                linhas,
                indice_competencia,
            )
        )

        inicio = indice_tipo

        if posicao + 1 < len(competencias):
            proxima_competencia = competencias[
                posicao + 1
            ]

            _, inicio_proximo_bloco = (
                extrair_tipo_folha(
                    linhas,
                    proxima_competencia,
                )
            )

            fim = inicio_proximo_bloco

        else:
            fim = len(linhas)

        texto_bloco = "\n".join(
            linhas[inicio:fim]
        )

        blocos.append(
            {
                "month": mes,
                "year": ano,
                "sheet_type": tipo_folha,
                "text": texto_bloco,
            }
        )

    return blocos


def extrair_bases_linha(
    linha: str,
) -> tuple[list[BaseValue], str]:
    """
    Extrai as bases existentes em uma linha.

    Exemplo:

        BASEDECALCULODOINSS 2.064,79
        VALORDOFGTS 165,18

    Também devolve o restante da linha
    sem as bases.
    """

    bases = []

    texto_restante = linha

    for label in BASES:
        padrao = re.compile(
            rf"\b{re.escape(label)}\s+"
            rf"([\d.]+,\d{{2}})",
            flags=re.IGNORECASE,
        )

        resultado = padrao.search(
            texto_restante
        )

        if not resultado:
            continue

        value = resultado.group(1)

        bases.append(
            BaseValue(
                label=label,
                value=value,
            )
        )

        texto_restante = (
            texto_restante[
                :resultado.start()
            ]
            + texto_restante[
                resultado.end():
            ]
        ).strip()

    return bases, texto_restante


def extrair_field_com_codigo(
    texto: str,
    kind: str,
) -> Field | None:
    """
    Extrai uma verba que possui código.

    Exemplos:

        37 DSR Adicional 19,23 28,03
        290 VA Funcionario 0 46,00
        102 Hr Ext Diu 60% 8,48 116,66
    """

    resultado = re.match(
        r"^\s*"
        r"(\d{1,4})"
        r"\s+"
        r"(.+?)"
        r"\s+"
        r"(\d+(?:[.,]\d+)?)"
        r"\s+"
        r"([\d.]+,\d{2})"
        r"\s*$",
        texto,
    )

    if not resultado:
        return None

    return Field(
        code=resultado.group(1),
        label=resultado.group(2).strip(),
        reference=resultado.group(3),
        value=resultado.group(4),
        kind=kind,
    )


def extrair_field_sem_codigo(
    texto: str,
    kind: str,
) -> Field | None:
    """
    Extrai uma verba que não possui código explícito.

    Exemplos:

        REMUNERACAOMES 1.454,59
        DIAS/HORASTRAB 220,00
        TOT.RENDIMENTOS 2.064,79
        TOTALDESCONTOS 1.148,15
    """

    resultado = re.match(
        r"^\s*"
        r"(.+?)"
        r"\s+"
        r"([\d.]+,\d{2})"
        r"\s*$",
        texto,
    )

    if not resultado:
        return None

    return Field(
        code="",
        label=resultado.group(1).strip(),
        reference="",
        value=resultado.group(2),
        kind=kind,
    )


def extrair_totais_linha(
    linha: str,
) -> list[Field]:
    """
    Extrai totais que podem aparecer sozinhos
    ou juntos na mesma linha.

    Exemplos:

        TOT.RENDIMENTOS 2.064,79

        TOTALDESCONTOS 1.148,15

        TOT.RENDIMENTOS 2.819,91
        TOTALDESCONTOS 0,00
    """

    fields = []

    padroes = [
        (
            "TOT.RENDIMENTOS",
            "rendimento",
        ),
        (
            "TOTALDESCONTOS",
            "desconto",
        ),
    ]

    for label, kind in padroes:
        resultado = re.search(
            rf"\b{re.escape(label)}\s+"
            rf"([\d.]+,\d{{2}})",
            linha,
            flags=re.IGNORECASE,
        )

        if not resultado:
            continue

        fields.append(
            Field(
                code="",
                label=label,
                reference="",
                value=resultado.group(1),
                kind=kind,
            )
        )

    return fields


def extrair_fields_linha(
    linha: str,
    somente_descontos: bool = False,
) -> list[Field]:
    """
    Extrai todas as verbas existentes em uma linha
    e identifica se pertencem a rendimentos ou descontos.

    Regras da ficha financeira:

    Antes de TOT.RENDIMENTOS:

        primeira verba da linha = rendimento
        demais verbas = desconto

    Depois de TOT.RENDIMENTOS:

        todas as verbas = desconto

    Também trata linhas como:

        TOT.RENDIMENTOS 25.043,34
        419 13º. Adto Desc 0 1.555,11

    onde o total e um desconto aparecem na mesma linha.
    """

    fields = []

    # -------------------------------------------------
    # EXTRAI TOTAIS SEM DESCARTAR O RESTANTE DA LINHA
    # -------------------------------------------------

    total_rendimentos = re.search(
        r"\bTOT\.RENDIMENTOS\s+"
        r"([\d.]+,\d{2})",
        linha,
        flags=re.IGNORECASE,
    )

    if total_rendimentos:

        fields.append(
            Field(
                code="",
                label="TOT.RENDIMENTOS",
                reference="",
                value=total_rendimentos.group(1),
                kind="rendimento",
            )
        )

        # Remove somente o total.
        #
        # Exemplo:
        #
        # TOT.RENDIMENTOS 25.043,34
        # 419 13º. Adto Desc 0 1.555,11
        #
        # vira:
        #
        # 419 13º. Adto Desc 0 1.555,11

        linha = (
            linha[:total_rendimentos.start()]
            + linha[total_rendimentos.end():]
        ).strip()

        # Tudo que estiver depois do total
        # pertence à coluna de descontos.

        somente_descontos = True

    total_descontos = re.search(
        r"\bTOTALDESCONTOS\s+"
        r"([\d.]+,\d{2})",
        linha,
        flags=re.IGNORECASE,
    )

    if total_descontos:

        fields.append(
            Field(
                code="",
                label="TOTALDESCONTOS",
                reference="",
                value=total_descontos.group(1),
                kind="desconto",
            )
        )

        linha = (
            linha[:total_descontos.start()]
            + linha[total_descontos.end():]
        ).strip()

    # Se após remover os totais não restar nada,
    # podemos finalizar.

    if not linha:
        return fields

    # -------------------------------------------------
    # LOCALIZA CÓDIGOS DE VERBAS
    # -------------------------------------------------
    #
    # Não podemos simplesmente procurar qualquer número,
    # pois referências como:
    #
    #     0 764,00
    #
    # poderiam ser confundidas com códigos.
    #
    # Um código deve ser seguido por:
    #
    #     descrição textual
    #
    # ou pelo formato encontrado no 13º salário:
    #
    #     371 13º Normal ...
    #     419 13º. Adto Desc ...
    #
    # Portanto aceitamos opcionalmente um primeiro token
    # numérico com caracteres anexados (13º, 13o., etc.)
    # antes de uma palavra.

    padrao_codigo = re.compile(
        r"(?<!\S)"
        r"\d{1,4}"
        r"(?="
        r"\s+"
        r"(?:\d+\S*\s+)?"
        r"[A-Za-zÀ-ÖØ-öø-ÿ]"
        r")"
    )

    resultados = list(
        padrao_codigo.finditer(
            linha
        )
    )

    # -------------------------------------------------
    # NÃO EXISTE VERBA COM CÓDIGO
    # -------------------------------------------------

    if not resultados:

        kind = (
            "desconto"
            if somente_descontos
            else "rendimento"
        )

        field = extrair_field_sem_codigo(
            linha,
            kind,
        )

        if field:
            fields.append(
                field
            )

        return fields

    # -------------------------------------------------
    # TEXTO ANTES DO PRIMEIRO CÓDIGO
    # -------------------------------------------------

    primeiro_codigo = resultados[0]

    prefixo = linha[
        :primeiro_codigo.start()
    ].strip()

    if prefixo:

        kind_prefixo = (
            "desconto"
            if somente_descontos
            else "rendimento"
        )

        field = extrair_field_sem_codigo(
            prefixo,
            kind_prefixo,
        )

        if field:
            fields.append(
                field
            )

    # -------------------------------------------------
    # VERBAS COM CÓDIGO
    # -------------------------------------------------

    for indice, resultado in enumerate(
        resultados
    ):

        inicio = resultado.start()

        if indice + 1 < len(resultados):
            fim = resultados[
                indice + 1
            ].start()

        else:
            fim = len(linha)

        trecho = linha[
            inicio:fim
        ].strip()

        # ---------------------------------------------
        # DEFINE O TIPO DA VERBA
        # ---------------------------------------------

        if somente_descontos:

            kind = "desconto"

        elif prefixo:

            # Exemplo:
            #
            # REMUNERACAOMES 1.454,59
            # 290 VA Funcionario 0 46,00
            #
            # prefixo   -> rendimento
            # código 290 -> desconto

            kind = "desconto"

        elif len(resultados) > 1:

            # Exemplo:
            #
            # 371 13º Normal ...
            # 419 13º Adto Desc ...
            #
            # primeira coluna -> rendimento
            # segunda coluna  -> desconto

            kind = (
                "rendimento"
                if indice == 0
                else "desconto"
            )

        else:

            kind = (
                "desconto"
                if somente_descontos
                else "rendimento"
            )

        field = extrair_field_com_codigo(
            trecho,
            kind,
        )

        if field:
            fields.append(
                field
            )

    return fields


def extrair_conteudo_bloco(
    texto_bloco: str,
) -> tuple[
    list[Field],
    list[BaseValue],
]:
    """
    Extrai todas as verbas e bases
    de um bloco de holerite.
    """

    fields = []
    bases = []

    linhas = texto_bloco.splitlines()

    somente_descontos = False

    for linha in linhas:

        # -------------------------------------------------
        # IGNORA TIPO DA FOLHA
        # -------------------------------------------------

        if any(
            tipo.lower()
            == linha.strip().lower()
            for tipo in TIPOS_FOLHA
        ):
            continue

        # -------------------------------------------------
        # IGNORA COMPETÊNCIA
        # -------------------------------------------------

        if re.search(
            r"M\S*s:\s*[a-z]{3}-\d{2}",
            linha,
            flags=re.IGNORECASE,
        ):
            continue

        # -------------------------------------------------
        # EXTRAI BASES
        # -------------------------------------------------

        bases_linha, linha_sem_bases = (
            extrair_bases_linha(
                linha
            )
        )

        bases.extend(
            bases_linha
        )

        if not linha_sem_bases:
            continue

        # -------------------------------------------------
        # EXTRAI VERBAS
        # -------------------------------------------------

        fields_linha = extrair_fields_linha(
            linha_sem_bases,
            somente_descontos=(
                somente_descontos
            ),
        )

        fields.extend(
            fields_linha
        )

        # -------------------------------------------------
        # FIM DA REGIÃO DE RENDIMENTOS
        # -------------------------------------------------

        if (
            "TOT.RENDIMENTOS"
            in linha_sem_bases.upper()
        ):
            somente_descontos = True

    return fields, bases


def extrair_holerite(
    texto: str,
) -> Holerite:
    """
    Extrai a ficha financeira completa.

    Para cada bloco são extraídos:

        - competência;
        - tipo da folha;
        - verbas;
        - bases.
    """

    blocos = extrair_blocos(
        texto
    )

    pages = []

    for numero_bloco, bloco in enumerate(
        blocos,
        start=1,
    ):
        fields, bases = extrair_conteudo_bloco(
            bloco["text"]
        )

        pages.append(
            Page(
                page=numero_bloco,
                year=str(
                    bloco["year"]
                ),
                month=str(
                    bloco["month"]
                ),
                sheet_type=bloco[
                    "sheet_type"
                ],
                fields=fields,
                bases=bases,
            )
        )

    return Holerite(
        pages=pages
    )