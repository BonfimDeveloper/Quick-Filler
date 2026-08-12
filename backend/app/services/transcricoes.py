from typing import Any
from uuid import uuid4


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