from pathlib import Path

from app.extractors.holerite import extrair_blocos
from app.services.pdf import extrair_texto


caminho = Path(
    "uploads/a4205666-c1a8-45ec-b98e-72331d2d5eca.pdf"
)

texto = extrair_texto(caminho)

blocos = extrair_blocos(texto)

for bloco in blocos:

    if (
        bloco["month"] == 9
        and bloco["year"] == 2018
        and bloco["sheet_type"] == "Folha Normal"
    ):
        print(
            "======================================"
        )
        print("BLOCO ORIGINAL - 09/2018")
        print(
            "======================================"
        )

        for numero, linha in enumerate(
            bloco["text"].splitlines(),
            start=1,
        ):
            print(
                f"{numero:03}: {repr(linha)}"
            )