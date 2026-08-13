from typing import List, Literal

from pydantic import BaseModel


class Punch(BaseModel):
    kind: Literal["IN", "OUT"]
    time_raw: str
    time_hhmm: str


class Day(BaseModel):
    date_raw: str
    punches: List[Punch]


class Page(BaseModel):
    page: int
    year: str
    month: str
    days: List[Day]


class CartaoPonto(BaseModel):
    pages: List[Page]