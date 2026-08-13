import pytest

from app.extractors.holerite import extrair_holerite
from app.extractors.holerite_mensal import extrair_holerite_mensal


CABECALHO = (
    "D E M O N S T R A T I V O D E "
    "P A G A M E N T O M E N S A L"
)


def test_extrai_holerite_mensal_no_contrato_publico():
    texto = f"""
{CABECALHO}
Período : 1/2020 Data Pagto: 31.01.2020
Cod. Descrição Unidade Proventos Descontos
0105 Dias Trabalhados 30,00 1.678,61
/314 Contr. INSS Remuneração 9,00 177,03
Total 1.678,61 177,03
Líquido 1.501,58
Base I.N.S.S. : 1.678,61 F.G.T.S. do Mês : 134,28
Base I.R.R.F. : 1.501,58 Base FGTS: 1.678,61
"""

    pagina = extrair_holerite_mensal(
        texto
    ).pages[0].model_dump()

    assert pagina["page"] == 1
    assert pagina["year"] == "2020"
    assert pagina["month"] == "01"
    assert set(pagina) == {
        "page",
        "year",
        "month",
        "fields",
        "bases",
    }
    assert pagina["fields"] == [
        {
            "code": "0105",
            "label": "Dias Trabalhados",
            "reference": "30,00",
            "value": "1.678,61",
        },
        {
            "code": "/314",
            "label": "Contr. INSS Remuneração",
            "reference": "9,00",
            "value": "177,03",
        },
    ]
    assert {
        "label": "Valor Líquido",
        "value": "1.501,58",
    } in pagina["bases"]


def test_preserva_uma_saida_por_pagina_e_ordem_das_competencias():
    texto = f"""
{CABECALHO}
Período : 12/2019
Cod. Descrição Unidade Proventos Descontos
0105 Salário 1.000,00
Total 1.000,00 0,00
{CABECALHO}
Período : 01/2020
Cod. Descrição Unidade Proventos Descontos
0105 Salário 1.000,00
Total 1.000,00 0,00
"""

    paginas = extrair_holerite_mensal(texto).pages

    assert [
        (pagina.page, pagina.month, pagina.year)
        for pagina in paginas
    ] == [
        (1, "12", "2019"),
        (2, "01", "2020"),
    ]


def test_recusa_layout_de_holerite_desconhecido():
    with pytest.raises(
        ValueError,
        match="Layout de holerite não reconhecido",
    ):
        extrair_holerite(
            "Documento sem estrutura conhecida"
        )
