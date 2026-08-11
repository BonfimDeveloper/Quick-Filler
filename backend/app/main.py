from fastapi import FastAPI

from app.routes.transcricoes import router as transcricoes_router


app = FastAPI()

app.include_router(transcricoes_router)


@app.get("/healthz")
def health():
    return {
        "status": "ok"
    }