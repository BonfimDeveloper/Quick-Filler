# from pathlib import Path

# from app.extractors.cartao_ponto import extrair_dias
# from app.services.pdf import extrair_texto


# caminho = Path("uploads/f6edba40-89bf-47c4-96ff-e2808b80665b.pdf")

# texto = extrair_texto(caminho)

# dias = extrair_dias(texto)

# print("Quantidade de dias encontrados:", len(dias))

# for dia in dias:
#     print(dia)


# from pathlib import Path

# from app.services.pdf import extrair_paginas


# caminho = Path("uploads/f6edba40-89bf-47c4-96ff-e2808b80665b.pdf")

# paginas = extrair_paginas(caminho)

# print("Quantidade de páginas:", len(paginas))

# for numero, pagina in enumerate(paginas, start=1):
#     print()
#     print("=" * 60)
#     print(f"PÁGINA {numero}")
#     print("=" * 60)
#     print("Quantidade de caracteres:", len(pagina))
#     print(pagina[:500])



# from pathlib import Path

# from app.extractors.cartao_ponto import extrair_dias
# from app.services.pdf import extrair_paginas


# caminho = Path("uploads/f6edba40-89bf-47c4-96ff-e2808b80665b.pdf")

# paginas = extrair_paginas(caminho)

# for numero, pagina in enumerate(paginas, start=1):
#     dias = extrair_dias(pagina)

#     print()
#     print("=" * 60)
#     print(f"PÁGINA {numero}")
#     print("=" * 60)
#     print("Quantidade de registros:", len(dias))

#     for dia in dias:
#         print(dia)



# from pathlib import Path

# from app.extractors.cartao_ponto import extrair_dias, agrupar_dias
# from app.services.pdf import extrair_paginas


# caminho = Path("uploads/f6edba40-89bf-47c4-96ff-e2808b80665b.pdf")

# paginas = extrair_paginas(caminho)

# for numero, pagina in enumerate(paginas, start=1):
#     registros = extrair_dias(pagina)
#     dias = agrupar_dias(registros)

#     print()
#     print("=" * 60)
#     print(f"PÁGINA {numero}")
#     print("=" * 60)
#     print("Quantidade de dias:", len(dias))

#     for numero_dia, registros_dia in dias.items():
#         print()
#         print(f"Dia {numero_dia}:")

#         for registro in registros_dia:
#             print("  ", registro)




# from pathlib import Path

# from app.extractors.cartao_ponto import (
#     extrair_dias,
#     agrupar_dias,
#     extrair_horarios,
# )

# from app.services.pdf import extrair_paginas


# caminho = Path("uploads/f6edba40-89bf-47c4-96ff-e2808b80665b.pdf")

# paginas = extrair_paginas(caminho)

# for numero, pagina in enumerate(paginas, start=1):
#     registros = extrair_dias(pagina)
#     dias = agrupar_dias(registros)

#     print()
#     print("=" * 60)
#     print(f"PÁGINA {numero}")
#     print("=" * 60)

#     for numero_dia, registros_dia in dias.items():
#         print()
#         print(f"Dia {numero_dia}:")

#         for registro in registros_dia:
#             horarios = extrair_horarios(registro)

#             print("  Registro:", registro)
#             print("  Horários:", horarios)

for numero_dia, registros_dia in dias.items():
    punches = extrair_punches(registros_dia)

    print()
    print(f"Dia {numero_dia}:")

    for punch in punches:
        print(
            f"  {punch.kind} - "
            f"{punch.time_hhmm}"
        )