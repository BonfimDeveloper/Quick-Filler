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
from fastapi.responses import Response

from app.services.transcricoes import (
    atualizar_caminho_arquivo,
    atualizar_transcricao,
    criar_transcricao,
    excluir_transcricao,
    listar_transcricoes,
    limpar_transcricoes_expiradas,
    obter_transcricao as obter_transcricao_service,
    processar_transcricao,
)
from app.services.planilhas import gerar_planilha

from app.services.uploads import (
    salvar_upload,
    validar_upload,
)

from app.schemas.transcricao import (
    TranscricaoCriadaResponse,
    TranscricaoAtualizarRequest,
    TranscricaoDetalheResponse,
    TranscricaoResumoResponse,
)


router = APIRouter(
    prefix="/api/transcricoes",
    tags=["Transcrições"],
)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
     response_model=TranscricaoCriadaResponse,
)
async def criar_transcricao_endpoint(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile = File(...),
    tipo: Literal[
        "cartao-ponto",
        "holerite",
    ] = Form(...),
):
    limpar_transcricoes_expiradas()
    await validar_upload(arquivo)

    id_transcricao = criar_transcricao(
        tipo
    )

    caminho = await salvar_upload(
        arquivo,
        id_transcricao,
    )

    atualizar_caminho_arquivo(
        id_transcricao,
        caminho,
    )

    background_tasks.add_task(
        processar_transcricao,
        id_transcricao,
        caminho,
    )

    return {
        "id": id_transcricao,
    }

@router.get(
    "",
    response_model=list[TranscricaoResumoResponse],
)
async def listar_transcricoes_endpoint():
    limpar_transcricoes_expiradas()
    return listar_transcricoes()


@router.get(
    "/{id_transcricao}",
    response_model=TranscricaoDetalheResponse,
)
async def obter_transcricao(
    id_transcricao: str,
):
    transcricao = obter_transcricao_service(
        id_transcricao
    )

    if transcricao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada",
        )

    return transcricao


@router.put(
    "/{id_transcricao}",
    response_model=TranscricaoDetalheResponse,
)
async def atualizar_transcricao_endpoint(
    id_transcricao: str,
    dados: TranscricaoAtualizarRequest,
):
    atualizada = atualizar_transcricao(
        id_transcricao,
        dados.value.model_dump(),
    )

    if not atualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada",
        )

    return obter_transcricao_service(
        id_transcricao
    )


@router.get("/{id_transcricao}/planilha")
async def baixar_planilha(
    id_transcricao: str,
    formato: Literal["xlsx", "csv", "json"] = "xlsx",
):
    transcricao = obter_transcricao_service(
        id_transcricao
    )

    if transcricao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada",
        )

    if transcricao.status != "concluido" or transcricao.value is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transcrição ainda não está concluída",
        )

    conteudo, media_type, nome = gerar_planilha(
        transcricao.tipo,
        transcricao.value.model_dump(),
        formato,
    )

    return Response(
        content=conteudo,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{nome}"'
        },
    )


@router.delete(
    "/{id_transcricao}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def excluir_transcricao_endpoint(
    id_transcricao: str,
):
    excluida = excluir_transcricao(
        id_transcricao
    )

    if not excluida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcrição não encontrada",
        )

    return None
