from fastapi import FastAPI

from app.database import Base, engine
from app.models.transcricao import Transcricao
from app.routes.transcricoes import router as transcricoes_router


Base.metadata.create_all(bind=engine)


app = FastAPI()

app.include_router(transcricoes_router)


@app.get("/healthz")
def health():
    return {
        "status": "ok"
    }