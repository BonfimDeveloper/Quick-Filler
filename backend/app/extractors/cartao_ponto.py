import re

from app.models.cartao_ponto import CartaoPonto, Day, Punch


# =========================================================
# PADRÕES
# =========================================================

PADRAO_DIA = re.compile(
    r"^\s*(\d{1,2})\s*-\s*[A-Z]{3}"
)

PADRAO_HORARIO = re.compile(
    r"\b\d{2}:\d{2}\b"
)


# =========================================================
# MÊS / ANO
# =========================================================

def extrair_mes_ano(texto: str) -> tuple[int, int]:
    """
    Extrai mês e ano do cabeçalho.

    Exemplo:
        Mes/Ano :  7 / 2012

    Retorna:
        (7, 2012)
    """

    resultado = re.search(
        r"Mes/Ano\s*:\s*(\d{1,2})\s*/\s*(\d{4})",
        texto,
    )

    if not resultado:
        raise ValueError(
            "Não foi possível identificar o mês e o ano."
        )

    mes = int(resultado.group(1))
    ano = int(resultado.group(2))

    return mes, ano


# =========================================================
# REGISTROS DOS DIAS
# =========================================================

def extrair_dias(texto: str) -> list[str]:
    """
    Extrai os registros físicos dos dias.

    Exemplo:

        2 - SEG 08:00 09:03 14:05 HE-BCO DE HORAS 00:13
                15:12 18:36 HE-REMUNERADA      00:13

    vira um único registro contendo as duas linhas.

    Caso o PDF repita um dia:

        17 - TER ...
        17 - TER ...

    os dois registros permanecem separados nesta etapa.
    Posteriormente serão agrupados por agrupar_dias().
    """

    linhas = texto.splitlines()

    registros: list[str] = []
    registro_atual: list[str] = []

    for linha in linhas:

        # =================================================
        # NOVO REGISTRO DE DIA
        # =================================================

        if PADRAO_DIA.match(linha):

            if registro_atual:
                registros.append(
                    "\n".join(registro_atual)
                )

            # Mantemos a linha original sem strip()
            # para preservar a estrutura física do relatório.
            registro_atual = [linha]

            continue

        # =================================================
        # LINHA DE CONTINUAÇÃO
        # =================================================

        if (
            registro_atual
            and PADRAO_HORARIO.search(linha)
        ):
            registro_atual.append(linha)

    # Último registro
    if registro_atual:
        registros.append(
            "\n".join(registro_atual)
        )

    return registros


# =========================================================
# NÚMERO DO DIA
# =========================================================

def extrair_numero_dia(
    registro: str,
) -> int | None:
    """
    Extrai o número do dia.

    Exemplo:

        17 - TER 08:00 ...

    Retorna:
        17
    """

    linhas = registro.splitlines()

    if not linhas:
        return None

    resultado = PADRAO_DIA.match(
        linhas[0]
    )

    if not resultado:
        return None

    return int(resultado.group(1))


# =========================================================
# EXTRAÇÃO DAS BATIDAS
# =========================================================

def extrair_horarios(
    registro: str,
) -> list[str]:
    """
    Extrai apenas as batidas reais do funcionário.

    Estrutura do relatório SIPON:

        Dia Semana Jornada Entrada Saida Ocorrencia Qtde


    Exemplo normal:

        2 - SEG 08:00 09:03 14:05 HE-BCO DE HORAS 00:13
                15:12 18:36 HE-REMUNERADA      00:13

    Resultado:

        09:03
        14:05
        15:12
        18:36


    O primeiro horário da primeira linha é sempre
    considerado a Jornada, e não uma batida.

    Valores da coluna Qtde, como:

        00:13
        00:38

    também não são considerados batidas.
    """

    linhas = registro.splitlines()

    if not linhas:
        return []

    horarios_ponto: list[str] = []

    # =====================================================
    # PRIMEIRA LINHA DO REGISTRO
    # =====================================================

    primeira_linha = linhas[0]

    resultado = re.match(
        r"""
        ^\s*
        \d{1,2}
        \s*-\s*
        [A-Z]{3}
        \s+
        (?P<jornada>\d{2}:\d{2})
        (?:
            \s+
            (?P<entrada>\d{2}:\d{2})
            \s+
            (?P<saida>\d{2}:\d{2})
        )?
        """,
        primeira_linha,
        re.VERBOSE,
    )

    if resultado:

        entrada = resultado.group("entrada")
        saida = resultado.group("saida")

        if entrada is not None:
            horarios_ponto.append(
                entrada
            )

        if saida is not None:
            horarios_ponto.append(
                saida
            )

    # =====================================================
    # LINHAS DE CONTINUAÇÃO
    # =====================================================

    for linha in linhas[1:]:

        horarios = PADRAO_HORARIO.findall(
            linha
        )

        # Uma linha de continuação normalmente possui:
        #
        # 15:12 18:36 HE-REMUNERADA 00:13
        #
        # Temos:
        #
        # 15:12 -> entrada
        # 18:36 -> saída
        # 00:13 -> Qtde
        #
        # Portanto utilizamos apenas os dois primeiros.
        #
        # Também atende:
        #
        # 14:35 18:36
        #
        # sem ocorrência/Qtde.

        if len(horarios) >= 2:
            horarios_ponto.extend(
                horarios[:2]
            )

    return horarios_ponto


# =========================================================
# CRIAÇÃO DOS PUNCHES
# =========================================================

def criar_punches(
    horarios: list[str],
) -> list[Punch]:
    """
    Converte os horários em Punch.

    Alternância:

        IN
        OUT
        IN
        OUT
        ...
    """

    punches: list[Punch] = []

    for indice, horario in enumerate(
        horarios
    ):

        kind = (
            "IN"
            if indice % 2 == 0
            else "OUT"
        )

        punches.append(
            Punch(
                kind=kind,
                time_raw=horario,
                time_hhmm=horario,
            )
        )

    return punches


# =========================================================
# EXTRAÇÃO DOS PUNCHES DE UM DIA
# =========================================================

def extrair_punches(
    registros: list[str],
) -> list[Punch]:
    """
    Extrai todas as batidas dos registros
    pertencentes ao mesmo dia.

    Necessário para casos como:

        17 - TER 08:00 09:09 13:01 ...
        17 - TER 08:00 14:16 18:50 ...

    Resultado esperado:

        IN  09:09
        OUT 13:01
        IN  14:16
        OUT 18:50
    """

    horarios: list[str] = []

    for registro in registros:

        horarios.extend(
            extrair_horarios(
                registro
            )
        )

    return criar_punches(
        horarios
    )


# =========================================================
# AGRUPAMENTO DOS DIAS
# =========================================================

def agrupar_dias(
    registros: list[str],
) -> dict[int, list[str]]:
    """
    Agrupa registros pelo número do dia.

    Exemplo:

        17 - TER ...
        17 - TER ...

    vira:

        {
            17: [
                registro_1,
                registro_2
            ]
        }
    """

    dias: dict[int, list[str]] = {}

    for registro in registros:

        numero_dia = extrair_numero_dia(
            registro
        )

        if numero_dia is None:
            continue

        dias.setdefault(
            numero_dia,
            []
        ).append(
            registro
        )

    return dias


# =========================================================
# CARTÃO DE PONTO COMPLETO
# =========================================================

def extrair_cartao_ponto(
    texto: str,
) -> CartaoPonto:
    """
    Extrai o cartão de ponto completo.

    Cada ocorrência do cabeçalho:

        F O L H A   DE   F R E Q U E N C I A

    inicia um novo bloco/página/mês.
    """

    # =====================================================
    # DIVISÃO DAS PÁGINAS
    # =====================================================

    blocos = re.split(
        r"""
        (?=
            F\s*O\s*L\s*H\s*A
            \s+DE\s+
            F\s*R\s*E\s*Q\s*U\s*E\s*N\s*C\s*I\s*A
        )
        """,
        texto,
        flags=re.VERBOSE,
    )

    pages = []

    numero_pagina = 0

    for bloco in blocos:

        # =================================================
        # REGISTROS
        # =================================================

        registros = extrair_dias(
            bloco
        )

        if not registros:
            continue

        # =================================================
        # MÊS / ANO
        # =================================================

        mes, ano = extrair_mes_ano(
            bloco
        )

        numero_pagina += 1

        # =================================================
        # AGRUPAMENTO DOS DIAS
        # =================================================

        dias_agrupados = agrupar_dias(
            registros
        )

        days: list[Day] = []

        # =================================================
        # CRIA OS DAYS
        # =================================================

        for numero_dia in sorted(
            dias_agrupados.keys()
        ):

            registros_do_dia = (
                dias_agrupados[numero_dia]
            )

            punches = extrair_punches(
                registros_do_dia
            )

            days.append(
                Day(
                    date_raw=str(numero_dia),
                    punches=punches,
                )
            )

        # =================================================
        # ADICIONA A PÁGINA
        # =================================================

        pages.append(
            {
                "page": numero_pagina,
                "year": str(ano),
                "month": str(mes),
                "days": days,
            }
        )

    return CartaoPonto(
        pages=pages
    )