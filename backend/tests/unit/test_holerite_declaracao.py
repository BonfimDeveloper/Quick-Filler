from app.extractors.holerite_declaracao import (
    extrair_holerite_declaracao,
)


def test_reconstroi_colunas_da_declaracao_de_remuneracao():
    texto = """
Declaração Remuneração - Folha de Pagamento
Mês/Ano: MÊS08/2018 Folha de Pagamento:
Remuneração Função Vl. Ref.:
Adiantamento 13o.:
Provisão FGTS:
5.017,04
3.094,31
495,09
Margem (30%): 1.113,97
2.494,96
0,00
4.351,55
1.837,08
6.188,63
ValorNomeVerba Base / Saldo / Benefício
3.059,94010 VENCIMENTO PADRAO-VP
-433,20     6.188,63803 PREVI PESSOAL PB2
Funcionário:
Folha de Pagamento: ACERTO08/2018Mês/Ano:
ValorNomeVerba Base / Saldo / Benefício
-12,89058 HORA EXTRA-BCO HORAS-CONV JULHO/18
"""

    pagina = extrair_holerite_declaracao(
        texto
    ).pages[0]

    assert (pagina.month, pagina.year) == (
        "08",
        "2018",
    )
    assert [field.model_dump() for field in pagina.fields] == [
        {
            "code": "010",
            "label": "VENCIMENTO PADRAO-VP",
            "reference": "",
            "value": "3.059,94",
        },
        {
            "code": "803",
            "label": "PREVI PESSOAL PB2",
            "reference": "6.188,63",
            "value": "-433,20",
        },
        {
            "code": "058",
            "label": "HORA EXTRA-BCO HORAS-CONV JULHO/18",
            "reference": "",
            "value": "-12,89",
        },
    ]
    assert pagina.bases[-1].model_dump() == {
        "label": "Proventos Bruto",
        "value": "6.188,63",
    }


def test_preserva_ordem_das_paginas_da_declaracao():
    pagina = """
Declaração Remuneração - Folha de Pagamento
Mês/Ano: MÊS{mes}/2018 Folha de Pagamento:
ValorNomeVerba Base / Saldo / Benefício
1.000,00010 VENCIMENTO PADRAO-VP
"""
    texto = pagina.format(mes="08") + pagina.format(
        mes="09"
    )

    resultado = extrair_holerite_declaracao(texto)

    assert [
        (item.page, item.month)
        for item in resultado.pages
    ] == [(1, "08"), (2, "09")]
