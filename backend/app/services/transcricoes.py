from pathlib import Path
from typing import Any
from uuid import uuid4

from app.extractors.cartao_ponto import extrair_cartao_ponto
from app.services.pdf import extrair_texto


transcricoes: dict[str, dict[str, Any]] = {}


def criar_transcricao(tipo: str) -> str:
    id_transcricao = str(uuid4())

    transcricoes[id_transcricao] = {
        "id": id_transcricao,
        "tipo": tipo,
        "status": "processando",
        "erro": None,
        "value": None,
    }

    return id_transcricao


def processar_transcricao(
    id_transcricao: str,
    caminho: Path,
) -> None:
    """
    Processa o PDF associado a uma transcrição.
    """

    transcricao = transcricoes.get(id_transcricao)

    if transcricao is None:
        return

    try:
        texto = extrair_texto(caminho)

        tipo = transcricao["tipo"]

        if tipo == "cartao-ponto":
            resultado = extrair_cartao_ponto(texto)

        else:
            raise ValueError(
                f"Tipo de transcrição não suportado nesta etapa: {tipo}"
            )

        transcricao["value"] = resultado.model_dump()
        transcricao["status"] = "concluido"
        transcricao["erro"] = None

    except Exception as erro:
        transcricao["status"] = "erro"
        transcricao["erro"] = str(erro)
        transcricao["value"] = None