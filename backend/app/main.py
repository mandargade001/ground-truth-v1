from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from asgi_correlation_id import CorrelationIdMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging

# Configure Logging
configure_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add Correlation ID Middleware
app.add_middleware(CorrelationIdMiddleware)

# Mount Static Files for Document Previews
app.mount("/static", StaticFiles(directory="/app/uploads"), name="static")

app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Uploads for Preview
# Ensure directory exists
import os
UPLOAD_DIR = "/app/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {"message": "Welcome to RAG Application API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
