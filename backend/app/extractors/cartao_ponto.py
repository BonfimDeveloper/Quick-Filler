import re

from app.models.cartao_ponto import CartaoPonto, Punch


def extrair_mes_ano(texto: str) -> tuple[int, int]:
    padrao = r"Mes/Ano\s*:\s*(\d{1,2})\s*/\s*(\d{4})"

    resultado = re.search(padrao, texto)

    if not resultado:
        raise ValueError("Não foi possível identificar o mês e o ano.")

    mes = int(resultado.group(1))
    ano = int(resultado.group(2))

    return mes, ano


def extrair_dias(texto: str) -> list[str]:
    linhas = texto.splitlines()

    dias = []

    for linha in linhas:
        if re.match(r"^\s*\d{1,2}\s*-\s*[A-Z]{3}", linha):
            dias.append(linha.strip())

    return dias




def agrupar_dias(registros: list[str]) -> dict[int, list[str]]:
    dias = {}

    for registro in registros:
        resultado = re.match(r"^\s*(\d{1,2})\s*-\s*[A-Z]{3}", registro)

        if not resultado:
            continue

        numero_dia = int(resultado.group(1))

        if numero_dia not in dias:
            dias[numero_dia] = []

        dias[numero_dia].append(registro)

    return dias



def extrair_horarios(registro: str) -> list[str]:
    horarios = re.findall(r"\b\d{2}:\d{2}\b", registro)

    if len(horarios) < 3:
        return horarios[1:]

    return horarios[1:3]




def extrair_punches(registros: list[str]) -> list[Punch]:
    horarios = []

    for registro in registros:
        horarios.extend(extrair_horarios(registro))

    return criar_punches(horarios)

    


def criar_punches(horarios: list[str]) -> list[Punch]:
    punches = []

    for indice, horario in enumerate(horarios):
        kind = "IN" if indice % 2 == 0 else "OUT"

        punches.append(
            Punch(
                kind=kind,
                time_raw=horario,
                time_hhmm=horario,
            )
        )

    return punches



def extrair_cartao_ponto(texto: str) -> CartaoPonto:
    ...