from celery import Celery
import asyncio
from asgiref.sync import async_to_sync
from sqlalchemy.future import select
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models import Document
from app.rag.ingestion import ingest_document

celery_app = Celery(
    "worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"
)

celery_app.conf.task_routes = {
    "app.worker.process_document_task": "main-queue"
}

@celery_app.task(acks_late=True)
def process_document_task(doc_id: int, file_path: str):
    """
    Async task to process document ingestion.
    """
    async def _process():
        async with AsyncSessionLocal() as db:
            from app.core.logging import logger
            log = logger.bind(task="process_document", doc_id=doc_id)
            
            document = None
            try:
                # 1. Get Document
                result = await db.execute(select(Document).where(Document.id == doc_id))
                document = result.scalars().first()
                if not document:
                    log.warning("document_not_found")
                    return

                log.info("processing_started", filename=document.filename)

                # 2. Update status to processing
                document.status = "processing"
                await db.commit()

                # 3. Run Ingestion
                await ingest_document(file_path, doc_id)

                # 4. Update status to indexed
                document.status = "indexed"
                await db.commit()
                log.info("processing_completed")
                
            except Exception as e:
                log.exception("processing_failed", error=str(e))
                # 5. Handle Failure
                if document:
                    try:
                        document.status = "failed"
                        document.error_message = str(e)
                        await db.commit()
                    except Exception as db_e:
                        log.error("failed_to_save_error_status", error=str(db_e))

    # Run async function in sync Celery task
    async_to_sync(_process)()
