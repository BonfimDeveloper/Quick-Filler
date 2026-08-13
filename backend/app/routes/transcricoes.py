from typing import Literal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.services.transcricoes import (
    criar_transcricao,
    processar_transcricao,
    transcricoes,
)
from app.services.uploads import (
    salvar_upload,
    validar_upload,
)


router = APIRouter(
    prefix="/api/transcricoes",
    tags=["Transcrições"],
)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
)
async def criar_transcricao_endpoint(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(...),
    tipo: Literal[
        "cartao-ponto",
        "holerite",
    ] = Form(...),
):
    await validar_upload(arquivo)

    id_transcricao = criar_transcricao(tipo)

    caminho = await salvar_upload(
        arquivo,
        id_transcricao,
    )

    background_tasks.add_task(
        processar_transcricao,
        id_transcricao,
        caminho,
    )

    return {
        "id": id_transcricao,
    }


@router.get("/{id_transcricao}")
async def obter_transcricao(
    id_transcricao: str,
):
    transcricao = transcricoes.get(
        id_transcricao
    )

    if transcricao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada",
        )

    return transcricao