"""
Content upload routes
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.db import get_db
from app.models.file import File as FileModel
from app.schemas.file import FileResponse, FileUploadResponse
from app.utils.file_manager import file_manager
from app.utils.logger import app_logger
from app.utils.text_extractor import text_extractor

router = APIRouter(prefix="/content", tags=["Content"])

# Add simple upload router for direct /upload endpoint
upload_router = APIRouter(tags=["Upload"])

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".mp3", ".mp4", ".wav", ".docx", ".doc", ".odt", ".rtf"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB (increased for audio/video files)


@upload_router.post("/upload")
async def upload_simple(
    file: UploadFile = File(...)
):
    """
    Simple upload endpoint - saves to storage/uploads/<id>/
    Supports: .txt, .pdf, .mp3, .mp4
    """
    import uuid
    import os
    from pathlib import Path
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in {".txt", ".pdf", ".mp3", ".mp4"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not supported. Allowed types: .txt, .pdf, .mp3, .mp4"
        )
    
    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    try:
        # Create unique ID and directory
        file_id = str(uuid.uuid4())
        upload_dir = Path("storage/uploads") / file_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create metadata
        metadata = {
            "id": file_id,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "upload_path": str(file_path)
        }
        
        # Save metadata
        metadata_path = upload_dir / "metadata.json"
        import json
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        app_logger.info(f"File uploaded: {file_id} - {file.filename}")
        
        # Extract text for document files
        extracted_text = None
        text_metadata = None
        extraction_status = "not_applicable"
        
        # Check if file is a document that can have text extracted
        document_extensions = {".txt", ".pdf"}
        if file_ext in document_extensions:
            try:
                app_logger.info(f"Extracting text from {file.filename}")
                extraction_result = text_extractor.extract_text(str(file_path))
                
                extracted_text = extraction_result.get("text", "")
                text_metadata = {
                    "word_count": extraction_result.get("word_count", 0),
                    "char_count": extraction_result.get("char_count", 0),
                    "pages": extraction_result.get("pages", 1),
                    "format": extraction_result.get("format", file_ext[1:]),
                    "encoding": extraction_result.get("encoding"),
                    "method": extraction_result.get("method")
                }
                extraction_status = "success"
                
                app_logger.info(f"Text extracted: {len(extracted_text)} characters, {text_metadata['word_count']} words")
                
            except Exception as e:
                app_logger.warning(f"Text extraction failed for {file.filename}: {e}")
                extraction_status = "failed"
                text_metadata = {"error": str(e)}
        
        return {
            "id": file_id,
            "file_id": file_id,  # Keep both for backward compatibility
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path),
            "file_type": file_ext,
            "content_type": file.content_type,
            "status": "uploaded",
            "message": "File uploaded successfully",
            "extracted_text": extracted_text,
            "text_metadata": text_metadata,
            "extraction_status": extraction_status
        }
        
    except Exception as e:
        app_logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    domain: Optional[str] = Form(None),
    source_language: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a content file for translation with text extraction
    
    Supported formats: TXT, PDF, MP3, MP4, WAV, DOCX, DOC, ODT, RTF
    Maximum size: 100 MB
    
    Returns file information along with extracted text (for document files)
    """
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Save file to disk
    try:
        saved_file = await file_manager.save_upload(file)
        
        # Create database entry
        db_file = FileModel(
            filename=saved_file["filename"],
            original_filename=file.filename,
            path=saved_file["file_path"],
            file_type=file_ext,
            size=saved_file["size"],
            domain=domain,
            source_language=source_language
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        app_logger.info(f"File uploaded: {file.filename}")
        
        # Extract text for document files
        extracted_text = None
        text_metadata = None
        extraction_status = "not_applicable"
        
        # Check if file is a document that can have text extracted
        document_extensions = {".txt", ".pdf", ".docx", ".doc", ".odt", ".rtf"}
        if file_ext in document_extensions:
            try:
                app_logger.info(f"Extracting text from {file.filename}")
                extraction_result = text_extractor.extract_text(saved_file["file_path"])
                
                extracted_text = extraction_result.get("text", "")
                text_metadata = {
                    "word_count": extraction_result.get("word_count", 0),
                    "char_count": extraction_result.get("char_count", 0),
                    "pages": extraction_result.get("pages", 1),
                    "format": extraction_result.get("format", file_ext[1:]),
                    "encoding": extraction_result.get("encoding"),
                    "method": extraction_result.get("method"),
                    "paragraphs": extraction_result.get("paragraphs"),
                    "tables": extraction_result.get("tables")
                }
                extraction_status = "success"
                
                app_logger.info(f"Text extracted: {len(extracted_text)} characters, {text_metadata['word_count']} words")
                
            except Exception as e:
                app_logger.warning(f"Text extraction failed for {file.filename}: {e}")
                extraction_status = "failed"
                text_metadata = {"error": str(e)}
        
        # Create enhanced response
        response_data = {
            "id": db_file.id,
            "filename": db_file.filename,
            "original_filename": db_file.original_filename,
            "path": db_file.path,
            "file_type": db_file.file_type,
            "size": db_file.size,
            "domain": db_file.domain,
            "source_language": db_file.source_language,
            "created_at": db_file.created_at,
            "extracted_text": extracted_text,
            "text_metadata": text_metadata,
            "extraction_status": extraction_status
        }
        
        return FileUploadResponse(**response_data)
    
    except Exception as e:
        app_logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading file"
        )


@router.get("/files", response_model=list[FileResponse])
async def list_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List uploaded files
    
    Shows all files (no user restrictions without auth)
    """
    files = db.query(FileModel).offset(skip).limit(limit).all()
    
    return files


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Get file details
    """
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Allow all users to access files without auth
    
    return file


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a file
    """
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Allow all users to delete files without auth
    
    # Delete from disk
    file_manager.delete_file(file.path)
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    app_logger.info(f"File deleted: {file.filename}")
    
    return None

