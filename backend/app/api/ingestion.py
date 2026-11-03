import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.graph.audit import write_batch
from app.graph.store import Neo4jGraphStore
from app.graph.writer import GraphWriter
from app.pipeline.orchestrator import IngestionOrchestrator
from services import cases as case_service

router = APIRouter(prefix="/cases/{case_id}", tags=["ingestion"])
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
MAX_UPLOAD_FILES = int(os.environ.get("MAX_UPLOAD_FILES", 20))


def _decode_upload(upload: UploadFile, content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            422,
            f"{upload.filename} is not UTF-8 text; scanned PDFs are unsupported.",
        )


@router.post("/documents")
async def ingest_documents(
    case_id: str,
    files: list[UploadFile] = File(...),
    append_mode: bool = False,
):
    try:
        case_service.require_case(case_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))

    if not files:
        raise HTTPException(422, "Upload at least one document.")
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(422, f"At most {MAX_UPLOAD_FILES} files may be uploaded.")

    documents = []
    rejected = []
    for upload in files:
        filename = upload.filename or "unnamed"
        suffix = filename.lower().rsplit(".", 1)[-1]
        if suffix not in {"txt", "text", "csv", "tsv"}:
            rejected.append(
                {
                    "filename": filename,
                    "error": "Unsupported format. TXT, CSV, and TSV files are supported.",
                }
            )
            continue
        content = await upload.read()
        if len(content) > MAX_UPLOAD_BYTES:
            rejected.append({
                "filename": filename,
                "error": f"File exceeds {MAX_UPLOAD_BYTES} bytes.",
            })
            continue
        if not content.strip():
            rejected.append({"filename": filename, "error": "File is empty."})
            continue
        documents.append(
            {
                "filename": filename,
                "text": _decode_upload(upload, content),
            }
        )

    if rejected and not documents:
        raise HTTPException(422, {"files": rejected})
    if not documents:
        raise HTTPException(422, "No processable text documents were uploaded.")

    writer = GraphWriter(Neo4jGraphStore(), audit=write_batch)
    orchestrator = IngestionOrchestrator(writer)
    result, summary = orchestrator.run(
        case_id,
        documents,
        append_mode=append_mode,
    )
    extraction_mode = os.getenv("EXTRACTION_MODE", "pretrained_only").strip().lower()
    return {
        "ok": True,
        "case_id": case_id,
        "extractor": extraction_mode,
        "files": len(documents),
        "rejected_files": rejected,
        "entities": len(result.entities),
        "edges": len(result.edges),
        "phones": result.diagnostics.get("phones", 0),
        "plates": result.diagnostics.get("plates", 0),
        "cdr_valid_rows": result.diagnostics.get("cdr_valid_rows", 0),
        "graph": summary,
        "diagnostics": result.diagnostics,
    }
