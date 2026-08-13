from pathlib import Path

import pytest

from app.services import pdf


class PaginaFalsa:
    def __init__(self, texto: str):
        self.texto = texto

    def extract_text(self) -> str:
        return self.texto


class ReaderFalso:
    def __init__(self, caminho: Path):
        self.pages = [
            PaginaFalsa(
                "Cabeçalho, competência, tabela de verbas, "
                "referências, valores, bases e totais. " * 3
            ),
            PaginaFalsa(""),
        ]


def test_usa_ocr_apenas_na_pagina_sem_texto(monkeypatch):
    chamadas_ocr = []

    monkeypatch.setattr(pdf, "PdfReader", ReaderFalso)
    monkeypatch.setattr(
        pdf,
        "extrair_texto_com_ocr",
        lambda caminho, numero: (
            chamadas_ocr.append(numero)
            or "Texto reconhecido pelo OCR"
        ),
    )

    paginas = pdf.extrair_paginas_detalhadas(
        Path("documento.pdf")
    )

    assert chamadas_ocr == [2]
    assert [pagina.origem for pagina in paginas] == [
        "texto",
        "ocr",
    ]
    assert paginas[1].texto == "Texto reconhecido pelo OCR"


def test_rodape_isolado_nao_e_considerado_texto_util():
    rodape = (
        "Assinado eletronicamente por: documento juntado "
        "em 20/10/2022 - Fls. 316"
    )

    assert not pdf.texto_e_util(rodape)


def test_erro_de_ocr_nao_vira_transcricao_vazia(monkeypatch):
    class ReaderVazio:
        def __init__(self, caminho: Path):
            self.pages = [PaginaFalsa("")]

    monkeypatch.setattr(pdf, "PdfReader", ReaderVazio)

    def falhar_ocr(caminho: Path, numero: int):
        raise RuntimeError("OCR indisponível")

    monkeypatch.setattr(
        pdf,
        "extrair_texto_com_ocr",
        falhar_ocr,
    )

    with pytest.raises(
        RuntimeError,
        match="OCR indisponível",
    ):
        pdf.extrair_texto(
            Path("escaneado.pdf")
        )
