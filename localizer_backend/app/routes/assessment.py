"""
Assessment translation routes
Handles JSON and CSV assessment file translation for educational content
"""
import os
import json
import csv
import time
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import SUPPORTED_LANGUAGES, get_settings
from app.services.assessment_processor import get_assessment_processor
from app.services.nlp_engine import AdvancedNLPEngine
from app.utils.logger import app_logger

settings = get_settings()

router = APIRouter(prefix="/assessment", tags=["Assessment Translation"])

ALLOWED_ASSESSMENT_FORMATS = {".json", ".csv"}
MAX_ASSESSMENT_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/translate")
async def translate_assessment(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    domain: Optional[str] = Form("education")
):
    """
    Translate assessment files (JSON or CSV) containing questions and options
    
    Input: .json or .csv file with educational content
    Steps:
    1. Parse assessment file (JSON/CSV)
    2. Identify text fields (questions, options, instructions)
    3. Translate each text field using IndicTrans2/LLaMA
    4. Save localized version in storage/outputs/
    
    Output: Translated assessment file in same format
    """
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target language '{target_language}' not supported. Choose from: {list(SUPPORTED_LANGUAGES.keys())}"
        )
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_ASSESSMENT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Assessment format not supported. Allowed: {', '.join(ALLOWED_ASSESSMENT_FORMATS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_ASSESSMENT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_ASSESSMENT_SIZE // (1024*1024)} MB"
        )
    
    assessment_processor = get_assessment_processor()
    
    try:
        # Save assessment file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        app_logger.info(f"Starting assessment translation: {file.filename} → {target_language}")
        start_time = time.time()
        
        # Validate assessment file
        file_format = file_ext[1:]  # Remove the dot
        validation = assessment_processor.validate_assessment_file(temp_file_path, file_format)
        
        if not validation["is_valid"]:
            raise ValueError(f"Invalid assessment file: {validation['error']}")
        
        # Parse assessment content based on format
        if file_format == 'json':
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                assessment_content = json.load(f)
            
        elif file_format == 'csv':
            assessment_content = []
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                # Auto-detect CSV delimiter
                sample = f.read(1024)
                f.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(f, delimiter=delimiter)
                assessment_content = list(reader)
        
        app_logger.info(f"Assessment parsed: {file_format.upper()} with {validation.get('estimated_text_fields', 0)} text fields")
        
        # Initialize NLP engine for translation
        nlp_engine = AdvancedNLPEngine()
        
        # Process assessment based on format
        if file_format == 'json':
            translation_result = assessment_processor.process_json_assessment(
                json_content=assessment_content,
                target_language=target_language,
                nlp_engine=nlp_engine,
                domain=domain
            )
        else:  # CSV
            translation_result = assessment_processor.process_csv_assessment(
                csv_content=assessment_content,
                target_language=target_language,
                nlp_engine=nlp_engine,
                domain=domain
            )
        
        if not translation_result["success"]:
            raise ValueError(f"Translation processing failed: {translation_result.get('error', 'Unknown error')}")
        
        translated_content = translation_result["translated_content"]
        
        # Save translated assessment
        output_filename = f"assessment_{target_language}_{int(time.time())}.{file_format}"
        save_result = assessment_processor.save_translated_assessment(
            translated_content=translated_content,
            original_format=file_format,
            target_language=target_language,
            output_filename=output_filename
        )
        
        if not save_result["success"]:
            raise ValueError(f"Failed to save translated assessment: {save_result.get('error', 'Unknown error')}")
        
        processing_time = time.time() - start_time
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        app_logger.info(f"Assessment translation completed in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "message": "Assessment translation completed successfully",
            "input_file": file.filename,
            "target_language": target_language,
            "domain": domain,
            "file_format": file_format,
            "validation_info": validation,
            "translation_stats": {
                "estimated_text_fields": validation.get("estimated_text_fields", 0),
                "rows_processed": translation_result.get("rows_processed", 1) if file_format == 'csv' else 1,
                "processing_time_seconds": processing_time
            },
            "output_file": save_result["output_filename"],
            "output_path": save_result["output_path"],
            "file_size_bytes": save_result["file_size_bytes"]
        }
        
    except Exception as e:
        app_logger.error(f"Assessment translation failed: {str(e)}")
        # Clean up temporary file on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment translation failed: {str(e)}"
        )


@router.post("/validate")
async def validate_assessment_format(
    file: UploadFile = File(...)
):
    """
    Validate assessment file format and provide analysis
    
    Input: .json or .csv assessment file
    Output: Validation results and content analysis
    """
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_ASSESSMENT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Assessment format not supported. Allowed: {', '.join(ALLOWED_ASSESSMENT_FORMATS)}"
        )
    
    assessment_processor = get_assessment_processor()
    
    try:
        # Save file temporarily for validation
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, mode='wb') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        app_logger.info(f"Validating assessment file: {file.filename}")
        
        # Validate assessment
        file_format = file_ext[1:]  # Remove the dot
        validation_result = assessment_processor.validate_assessment_file(temp_file_path, file_format)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        if validation_result["is_valid"]:
            return {
                "status": "valid",
                "message": "Assessment file is valid and ready for translation",
                "input_file": file.filename,
                "validation_results": validation_result,
                "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
                "recommended_domains": ["education", "training", "examination", "general"]
            }
        else:
            return {
                "status": "invalid",
                "message": f"Assessment file validation failed: {validation_result['error']}",
                "input_file": file.filename,
                "validation_results": validation_result
            }
        
    except Exception as e:
        app_logger.error(f"Assessment validation failed: {str(e)}")
        # Clean up temporary file on error
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment validation failed: {str(e)}"
        )


@router.get("/sample-formats")
async def get_sample_assessment_formats():
    """
    Get sample assessment file formats for JSON and CSV
    
    Output: Sample structures showing expected format for assessments
    """
    json_sample = {
        "assessment": {
            "title": "Sample Mathematics Quiz",
            "instructions": "Answer all questions to the best of your ability",
            "time_limit": 60,
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "What is 2 + 2?",
                    "options": [
                        "3",
                        "4",
                        "5",
                        "6"
                    ],
                    "correct_answer": "4",
                    "explanation": "Adding 2 and 2 gives us 4"
                },
                {
                    "id": 2,
                    "type": "text",
                    "question": "Explain the concept of multiplication",
                    "hint": "Think about repeated addition"
                }
            ]
        }
    }
    
    csv_sample_structure = {
        "headers": [
            "question_id", "question_type", "question", "option_a", 
            "option_b", "option_c", "option_d", "correct_answer", 
            "explanation", "hint", "difficulty"
        ],
        "sample_rows": [
            {
                "question_id": "1",
                "question_type": "multiple_choice",
                "question": "What is the capital of India?",
                "option_a": "Mumbai",
                "option_b": "New Delhi",
                "option_c": "Kolkata", 
                "option_d": "Chennai",
                "correct_answer": "New Delhi",
                "explanation": "New Delhi is the capital city of India",
                "hint": "Think about the political center",
                "difficulty": "easy"
            }
        ]
    }
    
    return {
        "status": "success",
        "message": "Sample assessment formats",
        "supported_formats": list(ALLOWED_ASSESSMENT_FORMATS),
        "json_sample": json_sample,
        "csv_sample": csv_sample_structure,
        "translatable_fields": [
            "question", "questions", "instruction", "instructions", 
            "explanation", "hint", "options", "choices", "title", 
            "description", "feedback", "note", "comment"
        ],
        "non_translatable_fields": [
            "id", "type", "correct_answer", "score", "points", 
            "difficulty", "time_limit", "created_date", "author"
        ]
    }


@router.get("/download/{filename}")
async def download_assessment(filename: str):
    """
    Download translated assessment file
    """
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment file not found"
        )
    
    # Determine media type based on file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext == '.json':
        media_type = "application/json"
    elif file_ext == '.csv':
        media_type = "text/csv"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )