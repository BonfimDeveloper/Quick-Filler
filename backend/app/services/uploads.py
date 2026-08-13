from pathlib import Path

from fastapi import HTTPException, UploadFile, status


from app.config import MAX_UPLOAD_SIZE, UPLOADS_DIR


ALLOWED_CONTENT_TYPE = "application/pdf"
PDF_SIGNATURE = b"%PDF"


async def validar_upload(arquivo: UploadFile) -> None:
    if arquivo.content_type != ALLOWED_CONTENT_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo precisa ser um PDF.",
        )

    tamanho = 0

    while chunk := await arquivo.read(1024 * 1024):
        tamanho += len(chunk)

        if tamanho > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="O arquivo excede o tamanho máximo permitido de 10 MB.",
            )

    await arquivo.seek(0)

    assinatura = await arquivo.read(len(PDF_SIGNATURE))
    await arquivo.seek(0)

    if assinatura != PDF_SIGNATURE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O conteúdo do arquivo não corresponde a um PDF válido.",
        )


async def salvar_upload(arquivo: UploadFile, id_transcricao: str) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    caminho = UPLOADS_DIR / f"{id_transcricao}.pdf"

    with caminho.open("wb") as destino:
        while chunk := await arquivo.read(1024 * 1024):
            destino.write(chunk)

    await arquivo.seek(0)

    return caminho