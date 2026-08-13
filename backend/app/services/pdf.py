from dataclasses import dataclass
import os
from pathlib import Path
import shutil

from pypdf import PdfReader

from app.config import (
    BASE_DIR,
    TESSDATA_DIR,
    TESSERACT_CMD,
)


MIN_CARACTERES_TEXTO = 100


@dataclass(frozen=True)
class PaginaExtraida:
    numero: int
    texto: str
    origem: str


def texto_e_util(texto: str) -> bool:
    """Evita considerar rodapés isolados como conteúdo do documento."""

    caracteres = sum(
        caractere.isalnum()
        for caractere in texto
    )

    return caracteres >= MIN_CARACTERES_TEXTO


def extrair_texto_com_ocr(
    caminho: Path,
    numero_pagina: int,
) -> str:
    """Renderiza uma página e aplica OCR com Tesseract."""

    try:
        import fitz
        import pytesseract
    except ImportError as erro:
        raise RuntimeError(
            "O PDF não possui texto legível e o suporte a OCR "
            "não está instalado."
        ) from erro

    comando_tesseract = (
        TESSERACT_CMD
        or shutil.which("tesseract")
    )

    if comando_tesseract is None:
        caminho_padrao = Path(
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        if caminho_padrao.exists():
            comando_tesseract = str(
                caminho_padrao
            )

    if comando_tesseract is not None:
        pytesseract.pytesseract.tesseract_cmd = (
            comando_tesseract
        )

    diretorio_idiomas = TESSDATA_DIR

    if diretorio_idiomas is None:
        diretorio_local = BASE_DIR / ".tessdata"

        if diretorio_local.exists():
            diretorio_idiomas = str(
                diretorio_local
            )

    if diretorio_idiomas:
        os.environ["TESSDATA_PREFIX"] = (
            diretorio_idiomas
        )

    try:
        with fitz.open(caminho) as documento:
            pagina = documento.load_page(
                numero_pagina - 1
            )
            imagem = pagina.get_pixmap(
                dpi=300,
                alpha=False,
            )

        texto = pytesseract.image_to_string(
            imagem.pil_image(),
            lang="por",
        )
    except pytesseract.TesseractNotFoundError as erro:
        raise RuntimeError(
            "O PDF não possui texto legível e o mecanismo "
            "Tesseract OCR não está disponível."
        ) from erro

    return texto


def extrair_paginas_detalhadas(
    caminho: Path,
) -> list[PaginaExtraida]:
    """Extrai cada página, usando OCR somente quando necessário."""

    reader = PdfReader(caminho)
    paginas: list[PaginaExtraida] = []

    for numero, pagina in enumerate(
        reader.pages,
        start=1,
    ):
        texto = pagina.extract_text() or ""
        origem = "texto"

        if not texto_e_util(texto):
            texto = extrair_texto_com_ocr(
                caminho,
                numero,
            )
            origem = "ocr"

        paginas.append(
            PaginaExtraida(
                numero=numero,
                texto=texto,
                origem=origem,
            )
        )

    return paginas


def analisar_pdf(caminho: Path) -> dict:
    paginas = extrair_paginas_detalhadas(
        caminho
    )

    return {
        "pages": len(paginas),
        "pages_data": [
            {
                "page": pagina.numero,
                "characters": len(pagina.texto),
                "source": pagina.origem,
                "text": pagina.texto,
            }
            for pagina in paginas
        ],
    }


def extrair_texto(caminho: Path) -> str:
    return "\n".join(
        pagina.texto
        for pagina in extrair_paginas_detalhadas(
            caminho
        )
    )


def extrair_paginas(caminho: Path) -> list[str]:
    return [
        pagina.texto
        for pagina in extrair_paginas_detalhadas(
            caminho
        )
    ]
