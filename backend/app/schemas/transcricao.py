from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models.cartao_ponto import CartaoPonto
from app.models.holerite import Holerite


StatusTranscricao = Literal[
    "processando",
    "concluido",
    "erro",
]


class TranscricaoCriadaResponse(BaseModel):
    id: str


class TranscricaoResumoResponse(BaseModel):
    id: str
    tipo: Literal[
        "cartao-ponto",
        "holerite",
    ]
    status: StatusTranscricao
    erro: str | None
    created_at: datetime
    updated_at: datetime


class TranscricaoCartaoPontoResponse(BaseModel):
    id: str
    tipo: Literal["cartao-ponto"]
    status: StatusTranscricao
    erro: str | None
    value: CartaoPonto | None


class TranscricaoHoleriteResponse(BaseModel):
    id: str
    tipo: Literal["holerite"]
    status: StatusTranscricao
    erro: str | None
    value: Holerite | None


TranscricaoDetalheResponse = Annotated[
    TranscricaoCartaoPontoResponse
    | TranscricaoHoleriteResponse,
    Field(discriminator="tipo"),
]