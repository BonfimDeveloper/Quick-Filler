import csv
import json
from io import BytesIO, StringIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from app.models.cartao_ponto import CartaoPonto
from app.models.holerite import Holerite


COR_CABECALHO = "173772"


def linhas_cartao(
    cartao: CartaoPonto,
) -> tuple[list[str], list[list[str]]]:
    maior_quantidade = max(
        (
            len(day.punches)
            for page in cartao.pages
            for day in page.days
        ),
        default=0,
    )
    cabecalho = ["Data"]

    for indice in range(maior_quantidade):
        numero = indice // 2 + 1
        tipo = "Entrada" if indice % 2 == 0 else "Saída"
        cabecalho.append(f"{tipo} {numero}")

    linhas = []

    for page in cartao.pages:
        for day in page.days:
            horarios = [
                punch.time_hhmm
                for punch in day.punches
            ]
            linhas.append(
                [day.date_raw]
                + horarios
                + [""] * (maior_quantidade - len(horarios))
            )

    return cabecalho, linhas


def linhas_holerite(
    holerite: Holerite,
) -> tuple[list[str], list[list[str]]]:
    labels = []

    for page in holerite.pages:
        for field in page.fields:
            if field.label not in labels:
                labels.append(field.label)

    cabecalho = ["Pág.", "Mês", "Ano", *labels]
    linhas = []

    for page in holerite.pages:
        valores = {
            field.label: field.value
            for field in page.fields
        }
        linhas.append(
            [page.page, page.month, page.year]
            + [valores.get(label, "") for label in labels]
        )

    return cabecalho, linhas


def gerar_tabela(
    tipo: str,
    value: dict,
) -> tuple[list[str], list[list[str]]]:
    if tipo == "cartao-ponto":
        return linhas_cartao(
            CartaoPonto.model_validate(value)
        )

    if tipo == "holerite":
        return linhas_holerite(
            Holerite.model_validate(value)
        )

    raise ValueError("Tipo de transcrição não suportado.")


def gerar_csv(tipo: str, value: dict) -> bytes:
    cabecalho, linhas = gerar_tabela(tipo, value)
    arquivo = StringIO(newline="")
    escritor = csv.writer(arquivo)
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)

    return arquivo.getvalue().encode("utf-8-sig")


def gerar_xlsx(tipo: str, value: dict) -> bytes:
    cabecalho, linhas = gerar_tabela(tipo, value)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Transcrição"
    worksheet.append(cabecalho)

    for linha in linhas:
        worksheet.append(linha)

    preenchimento = PatternFill(
        fill_type="solid",
        fgColor=COR_CABECALHO,
    )

    for cell in worksheet[1]:
        cell.fill = preenchimento
        cell.font = Font(color="FFFFFF", bold=True)

    worksheet.freeze_panes = "A2"
    arquivo = BytesIO()
    workbook.save(arquivo)

    return arquivo.getvalue()


def gerar_planilha(
    tipo: str,
    value: dict,
    formato: str,
) -> tuple[bytes, str, str]:
    if formato == "json":
        return (
            json.dumps(value, ensure_ascii=False, indent=2).encode(),
            "application/json",
            "transcricao.json",
        )

    if formato == "csv":
        return (
            gerar_csv(tipo, value),
            "text/csv; charset=utf-8",
            "transcricao.csv",
        )

    if formato == "xlsx":
        return (
            gerar_xlsx(tipo, value),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "transcricao.xlsx",
        )

    raise ValueError("Formato de planilha não suportado.")
