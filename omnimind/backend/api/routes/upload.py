"""
OmniMind AI — POST /upload-pdf endpoint (Cloud Storage Enabled)
"""
import os
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from omnimind.db.base import get_db
from omnimind.db.models import User
from omnimind.db.crud import create_document, update_document_chunks
from omnimind.backend.api.dependencies import get_current_user
from omnimind.storage import get_storage_provider

logger = logging.getLogger("omnimind.backend.api.routes.upload")

router = APIRouter(prefix="/upload-pdf", tags=["Documents"])


@router.post(
    "",
    summary="Upload and index a PDF document to Cloud Storage & ChromaDB",
    response_description="Document metadata, storage URL, and indexing result",
    status_code=201,
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload and index"),
    collection_name: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a PDF file to S3/Supabase Storage, save locally for ingestion,
    index into ChromaDB, and record user document ownership.
    """
    from config import settings

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    file_content = await file.read()
    size_bytes = len(file_content)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    unique_id = str(uuid.uuid4())
    safe_name = f"{unique_id}_{file.filename.replace(' ', '_')}"
    dest_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    # 1. Save to local disk for RAG pipeline ingestion
    try:
        with open(dest_path, "wb") as f:
            f.write(file_content)
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 2. Upload to S3 / Cloud Storage
    storage = get_storage_provider()
    s3_key = storage.upload_file(file_content, safe_name, content_type="application/pdf")
    public_url = storage.get_public_url(s3_key)

    # 3. Create DB record bound to current_user
    col_name = collection_name or settings.CHROMA_COLLECTION_NAME
    doc = create_document(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        file_path=dest_path,
        file_size_bytes=size_bytes,
        collection_name=col_name,
        meta_data={"original_name": file.filename, "user_id": current_user.id, "public_url": public_url},
    )
    doc.s3_key = s3_key
    db.commit()

    # 4. Trigger ingestion task
    ingestion_result = {}
    try:
        from omnimind.worker.tasks import ingest_pdf_task
        task_result = ingest_pdf_task.delay(
            document_id=doc.id,
            file_path=dest_path,
            collection_name=col_name,
        )
        if hasattr(task_result, "result") and task_result.result:
            ingestion_result = task_result.result
            chunks = ingestion_result.get("chunks_ingested", 0)
            update_document_chunks(db, doc.id, chunks)
    except Exception as e:
        logger.warning(f"Ingestion task failed to dispatch: {e}")

    return JSONResponse(
        status_code=201,
        content={
            "message": "PDF uploaded to cloud storage and queued for ingestion.",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "file_size_bytes": size_bytes,
                "collection_name": col_name,
                "s3_key": s3_key,
                "public_url": public_url,
                "status": doc.status,
            },
            "ingestion": ingestion_result,
        },
    )
