"""
Integration API routes for NCVET/MSDE/Partner LMSs (Skill India Digital)
Provides REST endpoints for automatic content exchange and feedback
"""
import os
import json
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, List, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import SUPPORTED_LANGUAGES, get_settings
from app.services.nlp_engine import AdvancedNLPEngine
from app.services.speech_engine import get_speech_engine
from app.services.assessment_processor import get_assessment_processor
from app.services.video_processor import get_video_processor
from app.utils.logger import app_logger

settings = get_settings()

router = APIRouter(prefix="/integration", tags=["LMS Integration"])

# Job storage for tracking processing status
job_storage = {}

ALLOWED_INTEGRATION_FORMATS = {
    ".json", ".csv",  # Assessments
    ".txt", ".pdf", ".docx",  # Documents
    ".mp3", ".wav", ".mp4", ".avi", ".mov",  # Media
}
MAX_INTEGRATION_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


@router.post("/upload")
async def integration_upload(
    file: UploadFile = File(...),
    target_languages: str = Form(...),  # Comma-separated language codes
    content_type: str = Form(...),  # "assessment", "document", "audio", "video"
    domain: Optional[str] = Form("general"),
    partner_id: Optional[str] = Form(None),  # LMS/NCVET partner identifier
    callback_url: Optional[str] = Form(None),  # Optional webhook URL for completion notification
    priority: Optional[str] = Form("normal")  # "low", "normal", "high"
):
    """
    LMS/NCVET content upload endpoint for automatic localization
    
    Purpose: Enable automatic exchange of localized content
    
    Input: Content file + localization parameters
    Output: Job ID for tracking processing status
    
    Supported content types:
    - assessment: JSON/CSV files with questions and options
    - document: Text/PDF/DOCX files for translation
    - audio: MP3/WAV files for speech localization
    - video: MP4/AVI files for video localization with subtitles
    """
    # Parse target languages
    try:
        target_lang_list = [lang.strip() for lang in target_languages.split(",")]
        # Validate all languages
        invalid_languages = [lang for lang in target_lang_list if lang not in SUPPORTED_LANGUAGES]
        if invalid_languages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported languages: {invalid_languages}. Supported: {list(SUPPORTED_LANGUAGES.keys())}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid target_languages format. Use comma-separated language codes: {str(e)}"
        )
    
    # Validate content type
    valid_content_types = ["assessment", "document", "audio", "video"]
    if content_type not in valid_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type must be one of: {valid_content_types}"
        )
    
    # Validate file extension based on content type
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    expected_formats = {
        "assessment": {".json", ".csv"},
        "document": {".txt", ".pdf", ".docx"},
        "audio": {".mp3", ".wav", ".m4a", ".ogg"},
        "video": {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    }
    
    if file_ext not in expected_formats.get(content_type, set()):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File format {file_ext} not supported for content type '{content_type}'. Expected: {expected_formats.get(content_type, {})}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_INTEGRATION_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_INTEGRATION_FILE_SIZE // (1024*1024)} MB"
        )
    
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        upload_filename = f"integration_{job_id}_{file.filename}"
        upload_path = os.path.join(settings.UPLOAD_DIR, upload_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        with open(upload_path, 'wb') as f:
            f.write(content)
        
        # Create job record
        job_record = {
            "job_id": job_id,
            "status": "queued",
            "created_at": time.time(),
            "updated_at": time.time(),
            "file_info": {
                "original_filename": file.filename,
                "upload_filename": upload_filename,
                "upload_path": upload_path,
                "file_size_bytes": len(content),
                "content_type": content_type
            },
            "processing_params": {
                "target_languages": target_lang_list,
                "domain": domain,
                "partner_id": partner_id,
                "callback_url": callback_url,
                "priority": priority
            },
            "results": {},
            "errors": [],
            "progress": 0
        }
        
        # Store job record
        job_storage[job_id] = job_record
        
        app_logger.info(f"Integration upload received: {file.filename} → Job {job_id} ({content_type}, {len(target_lang_list)} languages)")
        
        # Start background processing immediately (synchronous as per requirement)
        await _process_integration_job(job_id)
        
        return {
            "status": "accepted",
            "message": "Content uploaded and processing started",
            "job_id": job_id,
            "partner_id": partner_id,
            "file_info": {
                "filename": file.filename,
                "size_bytes": len(content),
                "content_type": content_type
            },
            "processing_params": {
                "target_languages": target_lang_list,
                "domain": domain,
                "priority": priority
            },
            "estimated_completion_time": _estimate_completion_time(content_type, len(target_lang_list), len(content)),
            "status_check_url": f"/integration/results/{job_id}",
            "created_at": job_record["created_at"]
        }
        
    except Exception as e:
        app_logger.error(f"Integration upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )


@router.get("/results/{job_id}")
async def get_integration_results(job_id: str):
    """
    Get processing status and results for integration job
    
    Purpose: LMS fetches processed outputs
    
    Returns:
    - Job status (queued, processing, completed, failed)
    - Progress percentage
    - Available output files
    - Download URLs
    """
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job ID {job_id} not found"
        )
    
    job_record = job_storage[job_id]
    
    # Calculate processing statistics
    processing_time = time.time() - job_record["created_at"]
    
    response = {
        "job_id": job_id,
        "status": job_record["status"],
        "progress": job_record["progress"],
        "created_at": job_record["created_at"],
        "updated_at": job_record["updated_at"],
        "processing_time_seconds": processing_time,
        "file_info": job_record["file_info"],
        "processing_params": job_record["processing_params"]
    }
    
    # Add results if processing is complete
    if job_record["status"] == "completed":
        response.update({
            "results": job_record["results"],
            "download_urls": {
                lang: f"/integration/download/{job_id}/{lang}/{filename}"
                for lang, files in job_record["results"].items()
                for filename in files.get("output_files", [])
            },
            "summary": {
                "languages_processed": len(job_record["results"]),
                "total_output_files": sum(len(files.get("output_files", [])) for files in job_record["results"].values()),
                "success_rate": len([r for r in job_record["results"].values() if r.get("success", False)]) / max(1, len(job_record["results"]))
            }
        })
    
    # Add errors if any
    if job_record["errors"]:
        response["errors"] = job_record["errors"]
    
    # Add estimated completion time if still processing
    if job_record["status"] in ["queued", "processing"]:
        content_type = job_record["file_info"]["content_type"]
        target_count = len(job_record["processing_params"]["target_languages"])
        file_size = job_record["file_info"]["file_size_bytes"]
        
        response["estimated_completion_seconds"] = _estimate_completion_time(content_type, target_count, file_size)
    
    return response


@router.post("/feedback")
async def submit_integration_feedback(
    job_id: str = Form(...),
    partner_id: Optional[str] = Form(None),
    quality_rating: Optional[int] = Form(None),  # 1-5 stars
    accuracy_rating: Optional[int] = Form(None),  # 1-5 stars
    usefulness_rating: Optional[int] = Form(None),  # 1-5 stars
    feedback_comments: Optional[str] = Form(None),
    language_specific_feedback: Optional[str] = Form(None),  # JSON string with per-language feedback
    learner_feedback: Optional[str] = Form(None),  # Feedback from end learners
    improvement_suggestions: Optional[str] = Form(None)
):
    """
    Submit quality and learner feedback for processed content
    
    Purpose: LMS sends quality feedback for continuous improvement
    
    Input: Job ID + quality ratings + feedback comments
    Output: Feedback acknowledgment and processing for model improvement
    """
    # Validate job ID
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job ID {job_id} not found"
        )
    
    job_record = job_storage[job_id]
    
    # Validate ratings
    ratings = [quality_rating, accuracy_rating, usefulness_rating]
    for rating in ratings:
        if rating is not None and (rating < 1 or rating > 5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ratings must be between 1 and 5"
            )
    
    try:
        # Parse language-specific feedback if provided
        language_feedback = {}
        if language_specific_feedback:
            try:
                language_feedback = json.loads(language_specific_feedback)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format for language_specific_feedback"
                )
        
        # Create feedback record
        feedback_record = {
            "feedback_id": str(uuid.uuid4()),
            "job_id": job_id,
            "partner_id": partner_id,
            "submitted_at": time.time(),
            "ratings": {
                "quality": quality_rating,
                "accuracy": accuracy_rating,
                "usefulness": usefulness_rating,
                "average": sum(r for r in ratings if r is not None) / len([r for r in ratings if r is not None]) if any(ratings) else None
            },
            "feedback": {
                "comments": feedback_comments,
                "language_specific": language_feedback,
                "learner_feedback": learner_feedback,
                "improvement_suggestions": improvement_suggestions
            },
            "job_info": {
                "content_type": job_record["file_info"]["content_type"],
                "languages": job_record["processing_params"]["target_languages"],
                "domain": job_record["processing_params"]["domain"]
            }
        }
        
        # Save feedback to storage (append to feedback file)
        feedback_file_path = os.path.join(settings.STORAGE_DIR, "integration_feedback.jsonl")
        
        # Ensure storage directory exists
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        
        # Append feedback to JSONL file
        with open(feedback_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_record, ensure_ascii=False) + '\n')
        
        # Update job record with feedback
        if "feedback" not in job_record:
            job_record["feedback"] = []
        job_record["feedback"].append(feedback_record)
        job_record["updated_at"] = time.time()
        
        app_logger.info(f"Integration feedback received for job {job_id}: Quality={quality_rating}, Accuracy={accuracy_rating}")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_record["feedback_id"],
            "job_id": job_id,
            "partner_id": partner_id,
            "ratings_summary": feedback_record["ratings"],
            "submitted_at": feedback_record["submitted_at"],
            "feedback_usage": {
                "model_improvement": "Feedback will be used for model retraining",
                "quality_monitoring": "Ratings help monitor service quality",
                "service_enhancement": "Comments guide feature development"
            }
        }
        
    except Exception as e:
        app_logger.error(f"Integration feedback submission failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feedback submission failed: {str(e)}"
        )


@router.get("/download/{job_id}/{language}/{filename}")
async def download_integration_output(job_id: str, language: str, filename: str):
    """
    Download specific output file from integration job
    
    Purpose: LMS downloads processed localized content
    """
    if job_id not in job_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job ID {job_id} not found"
        )
    
    job_record = job_storage[job_id]
    
    if job_record["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job_id} is not completed (status: {job_record['status']})"
        )
    
    # Check if language and filename exist in results
    if language not in job_record["results"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{language}' not found in job results"
        )
    
    language_results = job_record["results"][language]
    if filename not in language_results.get("output_files", []):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found for language '{language}'"
        )
    
    # Construct file path
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output file not found on server"
        )
    
    # Determine media type
    file_ext = Path(filename).suffix.lower()
    media_type_map = {
        '.json': 'application/json',
        '.csv': 'text/csv',
        '.txt': 'text/plain',
        '.pdf': 'application/pdf',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.mp4': 'video/mp4',
        '.srt': 'text/plain'
    }
    media_type = media_type_map.get(file_ext, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@router.get("/status")
async def integration_service_status():
    """
    Get integration service status and statistics
    """
    # Calculate statistics
    total_jobs = len(job_storage)
    completed_jobs = len([job for job in job_storage.values() if job["status"] == "completed"])
    processing_jobs = len([job for job in job_storage.values() if job["status"] == "processing"])
    failed_jobs = len([job for job in job_storage.values() if job["status"] == "failed"])
    
    # Get feedback statistics
    feedback_file_path = os.path.join(settings.STORAGE_DIR, "integration_feedback.jsonl")
    feedback_count = 0
    if os.path.exists(feedback_file_path):
        with open(feedback_file_path, 'r', encoding='utf-8') as f:
            feedback_count = sum(1 for _ in f)
    
    return {
        "service_status": "operational",
        "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        "supported_content_types": ["assessment", "document", "audio", "video"],
        "job_statistics": {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "processing_jobs": processing_jobs,
            "failed_jobs": failed_jobs,
            "success_rate": completed_jobs / max(1, total_jobs)
        },
        "feedback_statistics": {
            "total_feedback_entries": feedback_count
        },
        "service_capabilities": {
            "max_file_size_mb": MAX_INTEGRATION_FILE_SIZE // (1024 * 1024),
            "supported_formats": list(ALLOWED_INTEGRATION_FORMATS),
            "processing_types": {
                "assessment": "JSON/CSV translation with educational terminology",
                "document": "Text/PDF translation with domain adaptation",
                "audio": "Speech-to-text, translation, and text-to-speech",
                "video": "Audio extraction, translation, and subtitle generation"
            }
        },
        "api_endpoints": {
            "upload": "/integration/upload",
            "results": "/integration/results/{job_id}",
            "feedback": "/integration/feedback",
            "download": "/integration/download/{job_id}/{language}/{filename}"
        }
    }


async def _process_integration_job(job_id: str):
    """
    Background processing for integration jobs (synchronous as per requirement)
    """
    if job_id not in job_storage:
        return
    
    job_record = job_storage[job_id]
    
    try:
        # Update job status
        job_record["status"] = "processing"
        job_record["updated_at"] = time.time()
        job_record["progress"] = 0
        
        content_type = job_record["file_info"]["content_type"]
        target_languages = job_record["processing_params"]["target_languages"]
        domain = job_record["processing_params"]["domain"]
        upload_path = job_record["file_info"]["upload_path"]
        
        app_logger.info(f"Processing integration job {job_id}: {content_type} → {len(target_languages)} languages")
        
        results = {}
        total_languages = len(target_languages)
        
        for idx, target_lang in enumerate(target_languages):
            try:
                app_logger.info(f"Processing language {idx + 1}/{total_languages}: {target_lang}")
                
                # Process based on content type
                if content_type == "assessment":
                    lang_result = await _process_assessment_job(upload_path, target_lang, domain, job_id)
                elif content_type == "document":
                    lang_result = await _process_document_job(upload_path, target_lang, domain, job_id)
                elif content_type == "audio":
                    lang_result = await _process_audio_job(upload_path, target_lang, domain, job_id)
                elif content_type == "video":
                    lang_result = await _process_video_job(upload_path, target_lang, domain, job_id)
                else:
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                results[target_lang] = lang_result
                
                # Update progress
                job_record["progress"] = int(((idx + 1) / total_languages) * 100)
                job_record["updated_at"] = time.time()
                
                app_logger.info(f"Language {target_lang} completed successfully")
                
            except Exception as e:
                app_logger.error(f"Failed to process language {target_lang}: {str(e)}")
                results[target_lang] = {
                    "success": False,
                    "error": str(e),
                    "output_files": []
                }
                job_record["errors"].append(f"Language {target_lang}: {str(e)}")
        
        # Update job completion
        job_record["status"] = "completed"
        job_record["progress"] = 100
        job_record["results"] = results
        job_record["updated_at"] = time.time()
        
        app_logger.info(f"Integration job {job_id} completed successfully")
        
    except Exception as e:
        app_logger.error(f"Integration job {job_id} failed: {str(e)}")
        job_record["status"] = "failed"
        job_record["errors"].append(f"Job processing failed: {str(e)}")
        job_record["updated_at"] = time.time()


async def _process_assessment_job(file_path: str, target_lang: str, domain: str, job_id: str) -> Dict:
    """Process assessment file translation"""
    assessment_processor = get_assessment_processor()
    nlp_engine = AdvancedNLPEngine()
    
    # Determine file format
    file_ext = Path(file_path).suffix.lower()[1:]
    
    if file_ext == 'json':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        result = assessment_processor.process_json_assessment(
            json_content=content,
            target_language=target_lang,
            nlp_engine=nlp_engine,
            domain=domain
        )
    else:  # CSV
        import csv
        content = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            content = list(reader)
        
        result = assessment_processor.process_csv_assessment(
            csv_content=content,
            target_language=target_lang,
            nlp_engine=nlp_engine,
            domain=domain
        )
    
    if result["success"]:
        # Save result
        output_filename = f"integration_{job_id}_{target_lang}_assessment.{file_ext}"
        save_result = assessment_processor.save_translated_assessment(
            translated_content=result["translated_content"],
            original_format=file_ext,
            target_language=target_lang,
            output_filename=output_filename
        )
        
        return {
            "success": True,
            "output_files": [save_result["output_filename"]],
            "file_info": save_result
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "output_files": []
        }


async def _process_document_job(file_path: str, target_lang: str, domain: str, job_id: str) -> Dict:
    """Process document translation"""
    from app.utils.text_extractor import TextExtractor
    
    try:
        app_logger.info(f"Starting document processing: {file_path} -> {target_lang}")
        nlp_engine = AdvancedNLPEngine()
        text_extractor = TextExtractor()
        
        # Extract text from document
        app_logger.info("Extracting text from document...")
        extraction_result = text_extractor.extract_text(file_path)
        text_content = extraction_result["text"]
        app_logger.info(f"Text extracted: {len(text_content)} characters")
        
    except Exception as e:
        app_logger.error(f"Text extraction failed: {e}")
        raise ValueError(f"Text extraction failed: {str(e)}")
    
    try:
        # Translate text
        app_logger.info(f"Translating text to {target_lang}...")
        translation_result = await nlp_engine.translate(
            text=text_content,
            source_language="auto",
            target_languages=[target_lang],
            domain=domain
        )
        
        app_logger.info(f"Translation result structure: {list(translation_result.keys())}")
        
        # Extract single language result
        target_result = translation_result["translations"][0]
        app_logger.info("Translation completed successfully")
        
    except Exception as e:
        app_logger.error(f"Translation failed: {e}")
        raise ValueError(f"Translation failed: {str(e)}")
    
    # Save translated document
    output_filename = f"integration_{job_id}_{target_lang}_document.txt"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(target_result["translated_text"])
    
    return {
        "success": True,
        "output_files": [output_filename],
        "translation_info": {
            "confidence_score": translation_result.get("confidence_score", 0.0),
            "source_length": len(text_content),
            "target_length": len(translation_result["translated_text"])
        }
    }


async def _process_audio_job(file_path: str, target_lang: str, domain: str, job_id: str) -> Dict:
    """Process audio localization"""
    speech_engine = get_speech_engine()
    nlp_engine = AdvancedNLPEngine()
    
    # STT
    stt_result = await speech_engine.speech_to_text(
        audio_path=file_path,
        language=None
    )
    
    # Translation
    translation_result = await nlp_engine.translate(
        text=stt_result["text"],
        source_language=stt_result["language"],
        target_languages=[target_lang],
        domain=domain
    )
    
    # Extract single language result
    target_result = translation_result["translations"][0]
    
    # TTS
    tts_result = await speech_engine.text_to_speech(
        text=target_result["translated_text"],
        language=target_lang
    )
    
    # Move to outputs
    output_filename = f"integration_{job_id}_{target_lang}_audio.mp3"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    import shutil
    shutil.copy2(tts_result["output_path"], output_path)
    
    return {
        "success": True,
        "output_files": [output_filename],
        "processing_info": {
            "source_language": stt_result["language"],
            "confidence_score": translation_result.get("confidence_score", 0.0),
            "audio_duration": stt_result.get("duration", 0)
        }
    }


async def _process_video_job(file_path: str, target_lang: str, domain: str, job_id: str) -> Dict:
    """Process video localization"""
    video_processor = get_video_processor()
    speech_engine = get_speech_engine()
    nlp_engine = AdvancedNLPEngine()
    
    # Extract audio
    audio_result = video_processor.extract_audio_from_video(file_path)
    if not audio_result["success"]:
        raise ValueError(f"Audio extraction failed: {audio_result['error']}")
    
    # STT with timestamps
    stt_result = await speech_engine.speech_to_text_with_timestamps(
        audio_path=audio_result["audio_path"],
        language=None
    )
    
    # Translate segments
    translated_segments = []
    for segment in stt_result["segments"]:
        if segment["text"].strip():
            translation_result = await nlp_engine.translate(
                text=segment["text"].strip(),
                source_language=stt_result["language"],
                target_languages=[target_lang],
                domain=domain
            )
            
            # Extract single language result
            target_result = translation_result["translations"][0]
            
            translated_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "translated_text": target_result["translated_text"]
            })
    
    # Generate SRT subtitles
    srt_content = []
    for i, segment in enumerate(translated_segments, 1):
        start_time = _seconds_to_srt_time(segment["start"])
        end_time = _seconds_to_srt_time(segment["end"])
        
        srt_content.extend([
            str(i),
            f"{start_time} --> {end_time}",
            segment["translated_text"],
            ""
        ])
    
    # Save subtitles
    subtitle_filename = f"integration_{job_id}_{target_lang}_subtitles.srt"
    subtitle_path = os.path.join(settings.OUTPUT_DIR, subtitle_filename)
    
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(srt_content))
    
    # Clean up temp audio
    os.unlink(audio_result["audio_path"])
    
    return {
        "success": True,
        "output_files": [subtitle_filename],
        "processing_info": {
            "source_language": stt_result["language"],
            "segments_count": len(translated_segments),
            "video_duration": stt_result.get("duration", 0)
        }
    }


def _estimate_completion_time(content_type: str, language_count: int, file_size_bytes: int) -> int:
    """Estimate processing completion time in seconds"""
    base_times = {
        "assessment": 30,  # 30 seconds per language
        "document": 60,    # 1 minute per language
        "audio": 120,      # 2 minutes per language
        "video": 300       # 5 minutes per language
    }
    
    base_time = base_times.get(content_type, 60)
    size_factor = min(file_size_bytes / (10 * 1024 * 1024), 5)  # Max 5x for large files
    
    return int(base_time * language_count * (1 + size_factor))


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"