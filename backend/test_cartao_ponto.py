from pathlib import Path

from app.services.pdf import extrair_texto
from app.extractors.cartao_ponto import extrair_cartao_ponto


caminho = Path(
    "uploads/61adfbc4-1699-4178-8ff4-cb0fed62f3e0.pdf"
)

texto = extrair_texto(caminho)


# =========================================================
# DEBUG DO TEXTO EXTRAÍDO
# =========================================================

print("========== PRIMEIRAS LINHAS ==========")

for linha in texto.splitlines()[:80]:
    print(repr(linha))

print("======================================")


# =========================================================
# EXECUTA O PARSER
# =========================================================

resultado = extrair_cartao_ponto(texto)


# =========================================================
# MOSTRA TODAS AS BATIDAS ENCONTRADAS
# =========================================================

for page in resultado.pages:

    print()
    print(f"===== PÁGINA {page.page} =====")
    print(f"Mês/Ano: {page.month}/{page.year}")

    for day in page.days:

        if not day.punches:
            continue

        horarios = " | ".join(
            f"{p.kind} {p.time_hhmm}"
            for p in day.punches
        )

        print(
            f"Dia {day.date_raw}: {horarios}"
        )


# =========================================================
# CASOS IMPORTANTES PARA CONFERÊNCIA
# =========================================================

casos_para_testar = {
    (7, 2012): {1, 2, 4, 17, 27},
    (8, 2012): {15},
    (9, 2012): {19, 20, 24},
    (10, 2012): {2, 17},
    (11, 2012): {23},
}


print()
print("========== CASOS PARA CONFERÊNCIA ==========")

for page in resultado.pages:

    chave = (
        int(page.month),
        int(page.year),
    )

    dias_interesse = casos_para_testar.get(
        chave
    )

    if not dias_interesse:
        continue

    print()
    print(
        f"--- {page.month}/{page.year} ---"
    )

    for day in page.days:

        numero_dia = int(
            day.date_raw
        )

        if numero_dia not in dias_interesse:
            continue

        if day.punches:

            horarios = " | ".join(
                f"{p.kind} {p.time_hhmm}"
                for p in day.punches
            )

        else:
            horarios = "SEM BATIDAS"

        print(
            f"Dia {day.date_raw}: {horarios}"
        )


# =========================================================
# JSON COMPLETO
# =========================================================

print()
print("========== JSON ==========")

print(
    resultado.model_dump_json(
        indent=2
    )
)