from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api import deps
from app.db.session import get_db
from app.db.models import Document, User
from app.services import document_service

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    if not file.filename.endswith(('.txt', '.pdf', '.docx', '.md')):
        raise HTTPException(status_code=400, detail="File type not supported")
    
    document = await document_service.save_upload_file(file, current_user, db)
    return {"id": document.id, "filename": document.filename, "status": "uploading"}

@router.get("/", response_model=List[dict])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(select(Document).where(Document.owner_id == current_user.id))
    documents = result.scalars().all()
    # Simple serialization manual for now
    return [{
        "id": d.id, 
        "filename": d.filename, 
        "status": d.status, 
        "created_at": d.created_at,
        "preview_url": f"/static/uploads/{d.owner_id}_{d.filename}"
    } for d in documents]

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    success = await document_service.delete_document(doc_id, current_user, db)
    if not success:
         raise HTTPException(status_code=404, detail="Document not found")
    
    return {"status": "deleted", "id": doc_id}
