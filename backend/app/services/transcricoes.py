import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import select
from app.database import SessionLocal
from app.extractors.cartao_ponto import extrair_cartao_ponto
from app.extractors.holerite import extrair_holerite
from app.models.transcricao import Transcricao
from app.services.pdf import extrair_texto
from app.services.uploads import remover_upload
from app.schemas.transcricao import (
    TranscricaoCartaoPontoResponse,
    TranscricaoCriadaResponse,
    TranscricaoHoleriteResponse,
    TranscricaoResumoResponse,
)


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
) -> (
    TranscricaoCartaoPontoResponse
    | TranscricaoHoleriteResponse
    | None
):
    """
    Busca uma transcrição pelo ID.

    Retorna:
        TranscricaoCartaoPontoResponse
        TranscricaoHoleriteResponse
        None, caso não exista.
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

        if transcricao.tipo == "cartao-ponto":
            return TranscricaoCartaoPontoResponse(
                id=transcricao.id,
                tipo="cartao-ponto",
                status=transcricao.status,
                erro=transcricao.erro,
                value=value,
            )

        if transcricao.tipo == "holerite":
            return TranscricaoHoleriteResponse(
                id=transcricao.id,
                tipo="holerite",
                status=transcricao.status,
                erro=transcricao.erro,
                value=value,
            )

        raise ValueError(
            "Tipo de transcrição não suportado: "
            f"{transcricao.tipo}"
        )


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


def listar_transcricoes() -> list[TranscricaoResumoResponse]:
    """
    Lista todas as transcrições cadastradas.

    Retorna:
        Lista de TranscricaoResumoResponse.
    """

    with SessionLocal() as db:
        resultado = db.execute(
            select(Transcricao).order_by(
                Transcricao.created_at.desc()
            )
        )

        transcricoes = resultado.scalars().all()

        return [
            TranscricaoResumoResponse(
                id=transcricao.id,
                tipo=transcricao.tipo,
                status=transcricao.status,
                erro=transcricao.erro,
                created_at=transcricao.created_at,
                updated_at=transcricao.updated_at,
            )
            for transcricao in transcricoes
        ]


def excluir_transcricao(
    id_transcricao: str,
) -> bool:
    """
    Exclui uma transcrição do banco e remove
    o PDF associado, caso exista.

    Retorna:
        True  -> transcrição encontrada e excluída
        False -> transcrição não encontrada
    """

    with SessionLocal() as db:
        transcricao = db.get(
            Transcricao,
            id_transcricao,
        )

        if transcricao is None:
            return False

        caminho_arquivo = (
            Path(transcricao.caminho_arquivo)
            if transcricao.caminho_arquivo
            else None
        )

        if caminho_arquivo is not None:
            remover_upload(
                caminho_arquivo
            )

        db.delete(
            transcricao
        )

        db.commit()

        return True

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