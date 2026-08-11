from typing import List

from pydantic import BaseModel


class Field(BaseModel):
    code: str
    label: str
    reference: str
    value: str


class BaseValue(BaseModel):
    label: str
    value: str


class Page(BaseModel):
    page: int
    year: str
    month: str
    fields: List[Field]
    bases: List[BaseValue]


class Holerite(BaseModel):
    pages: List[Page]