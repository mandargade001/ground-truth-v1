from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
import tempfile
from openai import OpenAI
from app.core.config import settings

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    # Create temp file
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".webm"
    if not suffix:
        suffix = ".webm" # Default for browser recording
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
            
        return {"text": transcription.text}
        
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
