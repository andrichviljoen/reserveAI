from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.analyze import router as analyze_router
from app.routers.auth import router as auth_router
from app.routers.report import router as report_router
from app.routers.upload import router as upload_router

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(report_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
