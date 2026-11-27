
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ViennaTransitLab API",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/stops")
def get_stops():
    return [
        {
            "id": "mock-001",
            "name": "Stephansplatz",
            "latitude": 48.2083,
            "longitude": 16.3731,
            "transport_type": "metro"
        },
        {
            "id": "mock-002",
            "name": "Karlsplatz",
            "latitude": 48.2005,
            "longitude": 16.3695,
            "transport_type": "metro"
        },
        {
            "id": "mock-003",
            "name": "Schottentor",
            "latitude": 48.2156,
            "longitude": 16.3627,
            "transport_type": "tram"
        }
    ]
