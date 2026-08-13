from io import BytesIO

from openpyxl import load_workbook

from app.services.planilhas import gerar_csv, gerar_xlsx


def test_csv_cartao_cria_pares_conforme_maior_numero_de_batidas():
    value = {
        "pages": [
            {
                "page": 1,
                "days": [
                    {
                        "date_raw": "01/01/2020",
                        "punches": [
                            {"kind": "IN", "time_raw": "08:00", "time_hhmm": "08:00"},
                            {"kind": "OUT", "time_raw": "12:00", "time_hhmm": "12:00"},
                            {"kind": "IN", "time_raw": "13:00", "time_hhmm": "13:00"},
                        ],
                    }
                ],
            }
        ]
    }

    texto = gerar_csv("cartao-ponto", value).decode("utf-8-sig")

    assert "Data,Entrada 1,Saída 1,Entrada 2" in texto
    assert "01/01/2020,08:00,12:00,13:00" in texto


def test_xlsx_holerite_transpoe_verbas_e_formata_cabecalho():
    value = {
        "pages": [
            {
                "page": 1,
                "month": "01",
                "year": "2020",
                "fields": [
                    {"code": "001", "label": "Salário", "reference": "", "value": "1.000,00"}
                ],
                "bases": [],
            }
        ]
    }

    arquivo = gerar_xlsx("holerite", value)
    worksheet = load_workbook(BytesIO(arquivo)).active

    assert [cell.value for cell in worksheet[1]] == [
        "Pág.", "Mês", "Ano", "Salário"
    ]
    assert worksheet.cell(2, 4).value == "1.000,00"
    assert worksheet.cell(1, 1).fill.fgColor.rgb == "00173772"
