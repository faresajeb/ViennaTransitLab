from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

app = FastAPI(
    title="ViennaTransitLab API",
    description="Public transport analytics API for Vienna",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")