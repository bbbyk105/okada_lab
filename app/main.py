from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging
from app.routers import analyze

setup_logging()
app = FastAPI(title="DSA API")

# 必要に応じて許可オリジンを調整
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
