import pytest
from pydantic import ValidationError

from app.models.holerite import Holerite
from app.schemas.transcricao import TranscricaoAtualizarRequest


def test_put_aceita_value_tipado_com_paginas():
    dados = TranscricaoAtualizarRequest.model_validate(
        {
            "value": {
                "pages": [
                    {
                        "page": 1,
                        "year": "2020",
                        "month": "01",
                        "fields": [],
                        "bases": [],
                    }
                ]
            }
        }
    )

    assert isinstance(dados.value, Holerite)


def test_put_recusa_dicionario_generico_sem_pages():
    with pytest.raises(ValidationError):
        TranscricaoAtualizarRequest.model_validate(
            {"value": {"additionalProp1": {}}}
        )
