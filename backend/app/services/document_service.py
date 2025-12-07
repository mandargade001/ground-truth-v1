import os
import shutil
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import Document, User
from app.core.config import settings
from app.worker import process_document_task # Will implement this task next

UPLOAD_DIR = "/app/uploads" # For now storing locally in container

async def save_upload_file(upload_file: UploadFile, user: User, db: AsyncSession) -> Document:
    # 1. Create upload dir if not exists
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # 2. Save file to disk (or S3 in future)
    file_path = os.path.join(UPLOAD_DIR, f"{user.id}_{upload_file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save file")

    # 3. Create DB record
    db_document = Document(
        title=upload_file.filename,
        filename=upload_file.filename,
        s3_key=file_path, # Using local path as key for now
        media_type=upload_file.content_type,
        owner_id=user.id,
        status="pending"
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)

    # 4. Trigger Async Job
    process_document_task.delay(db_document.id, file_path)

    return db_document

async def delete_document(doc_id: int, user: User, db: AsyncSession):
    # 1. Get Document
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.owner_id == user.id))
    document = result.scalars().first()
    
    if not document:
        return False

    # 2. Delete from Vector DB (Chroma)
    from app.rag.ingestion import delete_document_from_vector_store
    delete_document_from_vector_store(doc_id)

    # 3. Delete File from Disk
    if document.s3_key and os.path.exists(document.s3_key):
        try:
            os.remove(document.s3_key)
        except Exception as e:
            print(f"Error deleting file {document.s3_key}: {e}")

    # 4. Delete from DB
    await db.delete(document)
    await db.commit()
    
    return True
