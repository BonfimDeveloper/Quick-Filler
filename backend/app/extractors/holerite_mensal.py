import re

from app.models.holerite import BaseValue, Field, Holerite, Page


PADRAO_CABECALHO = re.compile(
    r"D\s+E\s+M\s+O\s+N\s+S\s+T\s+R\s+A\s+T\s+I\s+V\s+O"
    r"\s+D\s+E\s+P\s+A\s+G\s+A\s+M\s+E\s+N\s+T\s+O"
    r"\s+M\s+E\s+N\s+S\s+A\s+L",
    re.IGNORECASE,
)

PADRAO_VALOR = re.compile(
    r"\d{1,3}(?:\.\d{3})*,\d{2}"
)


def reconhece_layout(texto: str) -> bool:
    return PADRAO_CABECALHO.search(texto) is not None


def dividir_paginas(texto: str) -> list[str]:
    partes = PADRAO_CABECALHO.split(texto)

    return [
        parte
        for parte in partes[1:]
        if parte.strip()
    ]


def extrair_competencia(texto: str) -> tuple[str, str]:
    resultado = re.search(
        r"Per[ií]odo\s*:\s*(\d{1,2})/(\d{4})",
        texto,
        flags=re.IGNORECASE,
    )

    if resultado is None:
        raise ValueError(
            "Não foi possível identificar a competência do holerite."
        )

    mes, ano = resultado.groups()

    return ano, mes.zfill(2)


def extrair_field(linha: str) -> Field | None:
    resultado_codigo = re.match(
        r"\s*(\S+)\s+(.+)",
        linha,
    )

    if resultado_codigo is None:
        return None

    codigo, restante = resultado_codigo.groups()
    valores = list(PADRAO_VALOR.finditer(restante))

    if not valores:
        return None

    label = restante[:valores[0].start()].strip()

    if not label:
        return None

    referencia = (
        valores[-2].group()
        if len(valores) >= 2
        else ""
    )

    return Field(
        code=codigo,
        label=label,
        reference=referencia,
        value=valores[-1].group(),
    )


def extrair_fields(texto: str) -> list[Field]:
    resultado = re.search(
        r"Cod\.\s*Descri[cç][aã]o\s+Unidade\s+"
        r"Proventos\s+Descontos\s*(.*?)\nTotal\s",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if resultado is None:
        return []

    fields = []

    for linha in resultado.group(1).splitlines():
        field = extrair_field(linha)

        if field is not None:
            fields.append(field)

    return fields


def extrair_bases(texto: str) -> list[BaseValue]:
    bases: list[BaseValue] = []

    total = re.search(
        r"^Total\s+(\S+)\s+(\S+)\s*$",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    if total:
        bases.extend(
            [
                BaseValue(
                    label="Total Proventos",
                    value=total.group(1),
                ),
                BaseValue(
                    label="Total Descontos",
                    value=total.group(2),
                ),
            ]
        )

    liquido = re.search(
        r"^L[ií]q[uü]ido\s+(\S+)\s*$",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    if liquido:
        bases.append(
            BaseValue(
                label="Valor Líquido",
                value=liquido.group(1),
            )
        )

    for linha in texto.splitlines():
        if not re.search(
            r"\b(?:Base|F\.G\.T\.S\.)",
            linha,
            flags=re.IGNORECASE,
        ):
            continue

        for resultado in re.finditer(
            r"(?P<label>Base\s+[^:]+|F\.G\.T\.S\.\s+do\s+M[eê]s)"
            r"\s*:\s*(?P<value>\d{1,3}(?:\.\d{3})*,\d{2})",
            linha,
            flags=re.IGNORECASE,
        ):
            bases.append(
                BaseValue(
                    label=resultado.group("label").strip(),
                    value=resultado.group("value"),
                )
            )

    return bases


def extrair_holerite_mensal(texto: str) -> Holerite:
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
                bases=extrair_bases(texto_pagina),
            )
        )

    return Holerite(pages=paginas)
