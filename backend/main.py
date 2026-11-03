import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.ingestion import router as documents_ingestion_router
from app.api.review import router as review_router
from routers import analysis, audit, cases, entities, graph, graph_edit, ingest
from utils.neo4j_driver import (
    Neo4jConnectionError,
    get_connection_error,
    verify_connectivity,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

app = FastAPI(title="SIH26189 Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ] or [
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(Neo4jConnectionError)
async def neo4j_connection_error_handler(_request, exc: Neo4jConnectionError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
            "code": "neo4j_unavailable",
        },
    )

app.include_router(cases.router)
app.include_router(ingest.router)
app.include_router(entities.router)
app.include_router(graph.router)
app.include_router(analysis.router)
app.include_router(audit.router)
app.include_router(graph_edit.router)
app.include_router(documents_ingestion_router)
app.include_router(review_router)


@app.on_event("startup")
def warm_up():
    # spaCy is optional until an artifact is configured. Keep startup available in
    # pretrained-only deployments; the extractor reports fallback diagnostics.
    return None


@app.get("/health")
def health():
    db_ok = verify_connectivity()
    response = {
        "status": "ok" if db_ok else "degraded",
        "service": "backend",
        "neo4j_connected": db_ok,
    }
    if not db_ok:
        response["neo4j_error"] = get_connection_error()
    return response


@app.get("/")
def root():
    return {"message": "SIH26189 backend is running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
