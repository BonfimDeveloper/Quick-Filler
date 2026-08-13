import re

from app.models.holerite import BaseValue, Field, Holerite, Page


MARCADOR_LAYOUT = "Declaração Remuneração - Folha de Pagamento"
VALOR = r"-?\d{1,3}(?:\.\d{3})*,\d{2}"

PADRAO_FIELD = re.compile(
    rf"^(?P<value>{VALOR})\s*"
    rf"(?:(?P<reference>{VALOR})\s*)?"
    r"(?P<code>\d{3})\s+"
    r"(?P<label>.+?)\s*$"
)


def reconhece_layout(texto: str) -> bool:
    return MARCADOR_LAYOUT.lower() in texto.lower()


def dividir_paginas(texto: str) -> list[str]:
    partes = re.split(
        rf"(?={re.escape(MARCADOR_LAYOUT)})",
        texto,
        flags=re.IGNORECASE,
    )

    return [
        parte
        for parte in partes
        if reconhece_layout(parte)
    ]


def extrair_competencia(texto: str) -> tuple[str, str]:
    resultado = re.search(
        r"M[eê]s/Ano:\s*(?:M[eê]S)?\s*(\d{1,2})/(\d{4})",
        texto,
        flags=re.IGNORECASE,
    )

    if resultado is None:
        raise ValueError(
            "Não foi possível identificar a competência do holerite."
        )

    mes, ano = resultado.groups()

    return ano, mes.zfill(2)


def extrair_fields(texto: str) -> list[Field]:
    fields = []

    for linha in texto.splitlines():
        resultado = PADRAO_FIELD.match(
            linha.strip()
        )

        if resultado is None:
            continue

        fields.append(
            Field(
                code=resultado.group("code"),
                label=resultado.group("label").strip(),
                reference=(
                    resultado.group("reference")
                    or ""
                ),
                value=resultado.group("value"),
            )
        )

    return fields


def extrair_bases_folha_principal(
    texto: str,
) -> list[BaseValue]:
    cabecalho, separador, _ = texto.partition(
        "ValorNomeVerba"
    )

    if not separador:
        return []

    valores = re.findall(VALOR, cabecalho)

    if len(valores) < 9:
        return []

    return [
        BaseValue(
            label="Remuneração Função",
            value=valores[0],
        ),
        BaseValue(
            label="Adiantamento 13º",
            value=valores[1],
        ),
        BaseValue(
            label="Provisão FGTS",
            value=valores[2],
        ),
        BaseValue(
            label="Proventos Retidos",
            value=valores[5],
        ),
        BaseValue(
            label="Proventos Líquidos",
            value=valores[6],
        ),
        BaseValue(
            label="Consignação",
            value=valores[7],
        ),
        BaseValue(
            label="Proventos Bruto",
            value=valores[8],
        ),
    ]


def extrair_holerite_declaracao(
    texto: str,
) -> Holerite:
    paginas = []

    for numero, texto_pagina in enumerate(
        dividir_paginas(texto),
        start=1,
    ):
        ano, mes = extrair_competencia(
            texto_pagina
        )

        paginas.append(
            Page(
                page=numero,
                year=ano,
                month=mes,
                fields=extrair_fields(texto_pagina),
                bases=extrair_bases_folha_principal(
                    texto_pagina
                ),
            )
        )

    return Holerite(pages=paginas)
