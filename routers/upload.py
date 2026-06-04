from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os
import uuid
from routers.auth import get_current_user_id

router = APIRouter(prefix="/upload", tags=["upload"])

# Directory where uploaded files will be stored
UPLOAD_DIR = "uploads"

# Create directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    # Validate extension
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: PDF, JPG, PNG, DOC, DOCX"
        )
        
    # Read file content and check size (Max: 5MB)
    contents = await file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the maximum limit of 5MB."
        )
        
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save the file
    with open(filepath, "wb") as buffer:
        buffer.write(contents)
        
    return {
        "url": f"/uploads/{unique_filename}",
        "filename": filename,
        "size": len(contents)
    }
