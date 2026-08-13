import pytest

from app.extractors.cartao_ponto import extrair_cartao_ponto


CABECALHO = "F O L H A   DE   F R E Q U E N C I A"


def test_preserva_ordem_datas_e_dias_sem_batidas():
    texto = f"""
{CABECALHO}
Mes/Ano : 7 / 2012
3 - TER 08:00 09:03 14:05
1 - DOM 08:00
2 - SEG 08:00 09:10 18:20
"""

    resultado = extrair_cartao_ponto(texto)

    assert [
        day.date_raw for day in resultado.pages[0].days
    ] == ["3", "1", "2"]
    assert resultado.pages[0].days[1].punches == []


def test_agrupa_data_repetida_sem_mudar_posicao():
    texto = f"""
{CABECALHO}
Mes/Ano : 7 / 2012
17 - TER 08:00 09:09 13:01
18 - QUA 08:00 09:14 18:46
17 - TER 08:00 14:16 18:50
"""

    resultado = extrair_cartao_ponto(texto)
    days = resultado.pages[0].days

    assert [day.date_raw for day in days] == ["17", "18"]
    assert [
        (punch.kind, punch.time_raw, punch.time_hhmm)
        for punch in days[0].punches
    ] == [
        ("IN", "09:09", "09:09"),
        ("OUT", "13:01", "13:01"),
        ("IN", "14:16", "14:16"),
        ("OUT", "18:50", "18:50"),
    ]


def test_preserva_data_completa_e_contrato_literal_da_pagina():
    texto = f"""
{CABECALHO}
Mes/Ano : 5 / 2019
21/05/2019 - TER 08:00 08:25 18:25
"""

    resultado = extrair_cartao_ponto(texto)
    pagina = resultado.pages[0].model_dump()

    assert pagina == {
        "page": 1,
        "days": [
            {
                "date_raw": "21/05/2019",
                "punches": [
                    {
                        "kind": "IN",
                        "time_raw": "08:25",
                        "time_hhmm": "08:25",
                    },
                    {
                        "kind": "OUT",
                        "time_raw": "18:25",
                        "time_hhmm": "18:25",
                    },
                ],
            }
        ],
    }


def test_recusa_layout_desconhecido_em_vez_de_retornar_vazio():
    with pytest.raises(
        ValueError,
        match="Layout de cartão de ponto não reconhecido",
    ):
        extrair_cartao_ponto(
            "Relatório sem estrutura conhecida"
        )
