from typing import Literal

from fastapi import APIRouter, File, Form, UploadFile, status


router = APIRouter(
    prefix="/api/transcricoes",
    tags=["Transcrições"],
)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def criar_transcricao(
    arquivo: UploadFile = File(...),
    tipo: Literal["cartao-ponto", "holerite"] = Form(...),
):
    return {
        "id": "abc123",
    }