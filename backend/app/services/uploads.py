from fastapi import HTTPException, UploadFile, status

from app.config import MAX_UPLOAD_SIZE


ALLOWED_CONTENT_TYPE = "application/pdf"


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