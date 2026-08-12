from pathlib import Path

from pypdf import PdfReader


def analisar_pdf(caminho: Path) -> dict:
    reader = PdfReader(caminho)

    paginas = []

    for numero, pagina in enumerate(reader.pages, start=1):
        texto = pagina.extract_text() or ""

        paginas.append(
            {
                "page": numero,
                "characters": len(texto),
                "text": texto,
            }
        )

    return {
        "pages": len(reader.pages),
        "pages_data": paginas,
    }

def extrair_texto(caminho: Path) -> str:
    reader = PdfReader(caminho)

    textos = []

    for pagina in reader.pages:
        texto = pagina.extract_text() or ""
        textos.append(texto)

    return "\n".join(textos)

def extrair_paginas(caminho: Path) -> list[str]:
    reader = PdfReader(caminho)

    paginas = []

    for pagina in reader.pages:
        texto = pagina.extract_text() or ""
        paginas.append(texto)

    return paginas