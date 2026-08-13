import json
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.extractors.cartao_ponto import extrair_cartao_ponto
from app.extractors.holerite import extrair_holerite
from app.models.transcricao import Transcricao
from app.services.pdf import extrair_texto


def criar_transcricao(
    tipo: str,
    caminho_arquivo: Path | None = None,
) -> str:
    """
    Cria uma nova transcrição no banco.

    Estado inicial:

        status = processando
        erro = None
        value = None
    """

    id_transcricao = str(uuid4())

    with SessionLocal() as db:
        transcricao = Transcricao(
            id=id_transcricao,
            tipo=tipo,
            status="processando",
            erro=None,
            value=None,
            caminho_arquivo=(
                str(caminho_arquivo)
                if caminho_arquivo
                else None
            ),
        )

        db.add(transcricao)
        db.commit()

    return id_transcricao


def obter_transcricao(
    id_transcricao: str,
) -> dict | None:
    """
    Busca uma transcrição pelo ID.

    Retorna None caso ela não exista.
    """

    with SessionLocal() as db:
        transcricao = db.get(
            Transcricao,
            id_transcricao,
        )

        if transcricao is None:
            return None

        value = None

        if transcricao.value:
            value = json.loads(
                transcricao.value
            )

        return {
            "id": transcricao.id,
            "tipo": transcricao.tipo,
            "status": transcricao.status,
            "erro": transcricao.erro,
            "value": value,
        }


def atualizar_caminho_arquivo(
    id_transcricao: str,
    caminho: Path,
) -> None:
    """
    Associa o PDF salvo à transcrição.
    """

    with SessionLocal() as db:
        transcricao = db.get(
            Transcricao,
            id_transcricao,
        )

        if transcricao is None:
            return

        transcricao.caminho_arquivo = str(
            caminho
        )

        db.commit()


def processar_transcricao(
    id_transcricao: str,
    caminho: Path,
) -> None:
    """
    Processa o PDF associado a uma transcrição.

    Fluxo:

        buscar transcrição no banco
                ↓
        extrair texto do PDF
                ↓
        identificar tipo
                ↓
        executar parser
                ↓
        serializar resultado
                ↓
        atualizar transcrição no banco
    """

    with SessionLocal() as db:
        transcricao = db.get(
            Transcricao,
            id_transcricao,
        )

        if transcricao is None:
            return

        try:
            texto = extrair_texto(
                caminho
            )

            tipo = transcricao.tipo

            if tipo == "cartao-ponto":
                resultado = extrair_cartao_ponto(
                    texto
                )

            elif tipo == "holerite":
                resultado = extrair_holerite(
                    texto
                )

            else:
                raise ValueError(
                    "Tipo de transcrição não "
                    f"suportado: {tipo}"
                )

            resultado_dict = (
                resultado.model_dump()
            )

            transcricao.value = json.dumps(
                resultado_dict,
                ensure_ascii=False,
            )

            transcricao.status = "concluido"
            transcricao.erro = None
            transcricao.caminho_arquivo = str(
                caminho
            )

            db.commit()

        except Exception as erro:
            db.rollback()

            transcricao = db.get(
                Transcricao,
                id_transcricao,
            )

            if transcricao is None:
                return

            transcricao.status = "erro"
            transcricao.erro = str(erro)
            transcricao.value = None
            transcricao.caminho_arquivo = str(
                caminho
            )

            db.commit()