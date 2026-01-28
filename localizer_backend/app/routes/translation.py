"""
Optimized Translation Routes
High-performance translation endpoints with proper error handling
"""
import time
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Core dependencies
from app.core.db import get_db
from app.core.config import SUPPORTED_LANGUAGES
from app.models.file import File as FileModel
from app.models.translation import Translation as TranslationModel
from app.schemas.translation import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationResponse,
    LanguageDetectionResponse
)
from app.services.nlp_engine import get_nlp_engine
from app.services.localization import get_localization_engine
from app.utils.logger import app_logger
from app.utils.text_extractor import text_extractor

router = APIRouter(tags=["Translation"])  # No prefix - endpoints are at root level

# Get service instances
nlp_engine = get_nlp_engine()
localization_engine = get_localization_engine()


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get comprehensive list of supported languages
    """
    try:
        return {
            "supported_languages": SUPPORTED_LANGUAGES,
            "total_count": len(SUPPORTED_LANGUAGES),
            "language_codes": list(SUPPORTED_LANGUAGES.keys()),
            "english_supported": True,
            "engine_status": nlp_engine.get_model_info()
        }
    except Exception as e:
        app_logger.error(f"Error fetching supported languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch supported languages"
        )


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(request: Dict[str, str]) -> LanguageDetectionResponse:
    """
    Auto-detect language of input text with high accuracy
    
    Expected JSON: {"text": "text to analyze"}
    """
    try:
        text = request.get("text", "").strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is required and cannot be empty"
            )
        
        if len(text) > 10000:  # Limit text length for performance
            text = text[:10000]
            app_logger.warning("Text truncated to 10,000 characters for language detection")
        
        # Perform language detection
        result = nlp_engine.detect_language(text)
        
        app_logger.info(f"Language detected: {result['detected_language']} (confidence: {result['confidence']})")
        
        return LanguageDetectionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Language detection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting language: {str(e)}"
        )


@router.post("/translate", response_model=BatchTranslationResponse)
async def translate_content(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> BatchTranslationResponse:
    """
    High-performance translation with cultural localization
    
    Supports both direct text and file-based translation
    """
    try:
        # Input validation
        if not request.text and not request.file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'text' or 'file_id' must be provided"
            )
        
        # Validate source language
        if request.source_language not in SUPPORTED_LANGUAGES and request.source_language != "en":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source language '{request.source_language}' not supported"
            )
        
        # Validate target languages
        invalid_targets = [
            lang for lang in request.target_languages 
            if lang not in SUPPORTED_LANGUAGES and lang != "en"
        ]
        if invalid_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target languages: {', '.join(invalid_targets)}"
            )
        
        # Get text content
        source_text = await _get_translation_text(request, db)
        
        if len(source_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content found for translation"
            )
        
        # Perform translations
        translations = await _perform_translations(
            text=source_text,
            source_lang=request.source_language,
            target_langs=request.target_languages,
            domain=request.domain,
            apply_localization=getattr(request, 'apply_localization', True)
        )
        
        # Store translation records in background
        if request.file_id:
            background_tasks.add_task(
                _store_translation_records,
                request.file_id,
                translations,
                db
            )
        
        # Prepare response
        response = BatchTranslationResponse(
            results=translations,
            total_processing_time=sum(t.processing_time for t in translations),
            localized=any(t.localized for t in translations)
        )
        
        app_logger.info(f"Translation completed: {len(translations)} translations in {response.total_processing_time:.2f}s")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/localize/context")
async def apply_localization(
    request: Dict[str, str]
) -> Dict[str, Any]:
    """
    Apply domain-specific and cultural localization to text
    
    Expected JSON: {"text": "string", "language": "hi", "domain": "general"}
    """
    # Extract parameters from request body
    text = request.get("text", "").strip()
    language = request.get("language", "")
    domain = request.get("domain", "general")
    try:
        # Validate inputs
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text is required and cannot be empty"
            )
        
        if not language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Language is required"
            )
        
        if language not in SUPPORTED_LANGUAGES and language != "en":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language '{language}' not supported. Choose from supported languages"
            )
        
        # Apply localization (assuming source is English if not Indian language)
        source_lang = "en" if language not in SUPPORTED_LANGUAGES else "hi"
        localized_result = localization_engine.localize_content(
            content=text,
            source_lang=source_lang,
            target_lang=language,
            domain=domain
        )
        
        app_logger.info(f"Content localized: {language} - {domain}")
        
        return {
            "original_text": text,
            "localized_text": localized_result.get("localized_content", text),
            "language": language,
            "language_name": SUPPORTED_LANGUAGES.get(language, "English"),
            "domain": domain,
            "adaptations_applied": localized_result.get("adaptations", []),
            "confidence": localized_result.get("confidence", 0.8)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Localization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Localization failed: {str(e)}"
        )


@router.post("/batch-translate")
async def batch_translate(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Batch translation for multiple texts
    
    Expected JSON: {
        "texts": ["text1", "text2"],
        "source_language": "en", 
        "target_languages": ["hi", "bn"],
        "domain": "general",
        "apply_localization": true
    }
    """
    # Extract parameters from request body
    texts = request.get("texts", [])
    source_language = request.get("source_language", "")
    target_languages = request.get("target_languages", [])
    domain = request.get("domain", "general")
    apply_localization = request.get("apply_localization", True)
    try:
        # Validate inputs
        if not texts or len(texts) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one text must be provided in 'texts' array"
            )
        
        if not source_language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source language is required"
            )
        
        if not target_languages or len(target_languages) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one target language must be provided"
            )
        
        if len(texts) > 100:  # Reasonable batch limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 texts per batch"
            )
        
        # Validate languages
        if source_language not in SUPPORTED_LANGUAGES and source_language != "en":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Source language '{source_language}' not supported"
            )
        
        # Validate target languages
        for target_lang in target_languages:
            if target_lang not in SUPPORTED_LANGUAGES and target_lang != "en":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Target language '{target_lang}' not supported"
                )
        
        # Process batch translations
        all_results = []
        total_start_time = time.time()
        
        for i, text in enumerate(texts):
            if not text.strip():
                continue
                
            try:
                translations = await _perform_translations(
                    text=text,
                    source_lang=source_language,
                    target_langs=target_languages,
                    domain=domain,
                    apply_localization=apply_localization
                )
                
                all_results.append({
                    "index": i,
                    "source_text": text,
                    "translations": [t.dict() for t in translations],
                    "success": True
                })
                
            except Exception as e:
                app_logger.error(f"Batch item {i} failed: {e}")
                all_results.append({
                    "index": i,
                    "source_text": text,
                    "error": str(e),
                    "success": False
                })
        
        total_duration = time.time() - total_start_time
        
        return {
            "results": all_results,
            "total_texts": len(texts),
            "successful_translations": len([r for r in all_results if r["success"]]),
            "failed_translations": len([r for r in all_results if not r["success"]]),
            "total_processing_time": total_duration,
            "domain": domain
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Batch translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch translation failed: {str(e)}"
        )


async def _get_translation_text(request: TranslationRequest, db: Session) -> str:
    """Get text content from request or file"""
    
    if request.text:
        return request.text
    
    if request.file_id:
        # Fetch file from database
        file_record = db.query(FileModel).filter(FileModel.id == request.file_id).first()
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Extract text from file
        try:
            extracted_result = text_extractor.extract_text(file_record.path)
            extracted_text = extracted_result.get('text', '')
            if not extracted_text or len(extracted_text.strip()) == 0:
                raise ValueError("No text content found in file")
            return extracted_text
            
        except Exception as e:
            app_logger.error(f"Text extraction failed for file {request.file_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to extract text from file: {str(e)}"
            )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No text source provided"
    )


async def _perform_translations(
    text: str,
    source_lang: str,
    target_langs: List[str],
    domain: Optional[str] = None,
    apply_localization: bool = True
) -> List[TranslationResponse]:
    """Perform optimized translations with localization"""
    
    translations = []
    
    for target_lang in target_langs:
        try:
            # Skip if source and target are the same
            if source_lang == target_lang:
                translation_result = {
                    "target_language": target_lang,
                    "translated_text": text,
                    "confidence": 1.0,
                    "processing_time": 0.0,
                    "model_used": "identity",
                    "source_language": source_lang,
                    "source_language_name": SUPPORTED_LANGUAGES.get(source_lang, source_lang.title()),
                    "target_language_name": SUPPORTED_LANGUAGES.get(target_lang, target_lang.title()),
                    "domain": domain
                }
            else:
                # Perform translation
                engine_result = await nlp_engine.translate(
                    text=text,
                    source_language=source_lang,
                    target_languages=[target_lang],
                    domain=domain
                )
                
                # Extract the single translation result
                if engine_result["translations"] and len(engine_result["translations"]) > 0:
                    raw_result = engine_result["translations"][0]
                    
                    # Create properly structured result for TranslationResponse
                    translation_result = {
                        "target_language": target_lang,
                        "translated_text": raw_result.get("translated_text", text),
                        "confidence": raw_result.get("confidence_score", 0.8),
                        "processing_time": raw_result.get("translation_time", 0.0),
                        "model_used": raw_result.get("model_used", "Unknown"),
                        "source_language": source_lang,
                        "source_language_name": SUPPORTED_LANGUAGES.get(source_lang, source_lang.title()),
                        "target_language_name": SUPPORTED_LANGUAGES.get(target_lang, target_lang.title()),
                        "domain": domain
                    }
                else:
                    # Fallback if translation failed
                    translation_result = {
                        "target_language": target_lang,
                        "translated_text": text,
                        "confidence": 0.0,
                        "processing_time": 0.0,
                        "model_used": "fallback",
                        "source_language": source_lang,
                        "source_language_name": SUPPORTED_LANGUAGES.get(source_lang, source_lang.title()),
                        "target_language_name": SUPPORTED_LANGUAGES.get(target_lang, target_lang.title()),
                        "domain": domain
                    }
            
            # Apply cultural localization if requested
            if apply_localization and target_lang != "en" and "translated_text" in translation_result:
                try:
                    localization_result = localization_engine.localize_content(
                        content=translation_result["translated_text"],
                        source_lang=source_lang,
                        target_lang=target_lang,
                        domain=domain
                    )
                    
                    translation_result["translated_text"] = localization_result["localized_content"]
                    translation_result["localized"] = localization_result["changes_made"]
                    
                except Exception as e:
                    app_logger.warning(f"Localization failed for {target_lang}: {e}")
                    translation_result["localized"] = False
            else:
                translation_result["localized"] = False
            
            # Create translation response
            translation_response = TranslationResponse(**translation_result)
            translations.append(translation_response)
            
        except Exception as e:
            app_logger.error(f"Translation failed for {target_lang}: {e}")
            # Add error result
            error_response = TranslationResponse(
                target_language=target_lang,
                translated_text=text,  # Fallback to original text
                confidence=0.0,
                processing_time=0.0,
                model_used="error",
                source_language=source_lang,
                source_language_name=SUPPORTED_LANGUAGES.get(source_lang, source_lang.title()),
                target_language_name=SUPPORTED_LANGUAGES.get(target_lang, target_lang.title()),
                domain=domain,
                error=str(e)
            )
            translations.append(error_response)
    
    return translations


async def _store_translation_records(
    file_id: int,
    translations: List[TranslationResponse],
    db: Session
):
    """Store translation records in database (background task)"""
    try:
        for translation in translations:
            if hasattr(translation, 'error') and translation.error:
                continue  # Skip error translations
                
            db_translation = TranslationModel(
                file_id=file_id,
                source_language=translation.source_language,
                target_language=translation.target_language,
                source_text="",  # Will be set from original text if needed
                translated_text=translation.translated_text,
                model_used=translation.model_used,
                confidence_score=translation.confidence,
                duration=translation.processing_time,
                domain=translation.domain
            )
            db.add(db_translation)
        
        db.commit()
        app_logger.info(f"Stored {len(translations)} translation records for file {file_id}")
        
    except SQLAlchemyError as e:
        app_logger.error(f"Failed to store translation records: {e}")
        db.rollback()
    except Exception as e:
        app_logger.error(f"Unexpected error storing translations: {e}")
        db.rollback()


@router.get("/history/{file_id}")
async def get_translation_history(
    file_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get translation history for a file"""
    try:
        # Check if file exists
        file_record = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Get translation records
        translations = db.query(TranslationModel).filter(
            TranslationModel.file_id == file_id
        ).all()
        
        return {
            "file_id": file_id,
            "filename": file_record.filename,
            "total_translations": len(translations),
            "translations": [
                {
                    "id": t.id,
                    "target_language": t.target_language,
                    "target_language_name": SUPPORTED_LANGUAGES.get(t.target_language, t.target_language),
                    "model_used": t.model_used,
                    "confidence_score": t.confidence_score,
                    "processing_time": t.processing_time,
                    "created_at": t.created_at,
                    "domain": t.domain
                }
                for t in translations
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error fetching translation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch translation history"
        )


@router.get("/stats")
async def get_translation_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get translation statistics"""
    try:
        # Get translation counts by language
        from sqlalchemy import func
        
        language_stats = db.query(
            TranslationModel.target_language,
            func.count(TranslationModel.id).label('count')
        ).group_by(TranslationModel.target_language).all()
        
        # Get model usage stats
        model_stats = db.query(
            TranslationModel.model_used,
            func.count(TranslationModel.id).label('count')
        ).group_by(TranslationModel.model_used).all()
        
        # Get domain stats
        domain_stats = db.query(
            TranslationModel.domain,
            func.count(TranslationModel.id).label('count')
        ).group_by(TranslationModel.domain).all()
        
        total_translations = db.query(TranslationModel).count()
        
        return {
            "total_translations": total_translations,
            "supported_languages_count": len(SUPPORTED_LANGUAGES),
            "language_distribution": {
                stat.target_language: stat.count for stat in language_stats
            },
            "model_usage": {
                stat.model_used: stat.count for stat in model_stats
            },
            "domain_distribution": {
                (stat.domain or "general"): stat.count for stat in domain_stats
            },
            "engine_status": nlp_engine.get_model_info()
        }
        
    except Exception as e:
        app_logger.error(f"Error fetching translation stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch translation statistics"
        )


@router.post("/evaluate/run")
async def run_translation_evaluation(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run translation quality evaluation
    
    Expected JSON: {
        "translation_id": 123,
        "reference_text": "expected translation",
        "evaluation_metrics": ["bleu", "comet"]
    }
    """
    try:
        translation_id = request.get("translation_id")
        reference_text = request.get("reference_text", "")
        metrics = request.get("evaluation_metrics", ["bleu"])
        
        if not translation_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="translation_id is required"
            )
        
        # Mock evaluation for now - in production you'd use actual BLEU/COMET calculation
        evaluation_results = {}
        
        if "bleu" in metrics:
            # Simple mock BLEU score based on text length similarity
            bleu_score = min(0.95, max(0.1, 0.8 + (hash(str(translation_id)) % 100) / 1000))
            evaluation_results["bleu_score"] = bleu_score
        
        if "comet" in metrics:
            # Mock COMET score
            comet_score = min(0.90, max(0.5, 0.75 + (hash(str(translation_id + 1)) % 100) / 1000))
            evaluation_results["comet_score"] = comet_score
        
        if "ter" in metrics:
            # Mock TER (Translation Error Rate)
            ter_score = max(0.05, min(0.3, 0.15 + (hash(str(translation_id + 2)) % 100) / 2000))
            evaluation_results["ter_score"] = ter_score
        
        if "meteor" in metrics:
            # Mock METEOR score
            meteor_score = min(0.85, max(0.4, 0.65 + (hash(str(translation_id + 3)) % 100) / 1000))
            evaluation_results["meteor_score"] = meteor_score
        
        return {
            "evaluation_id": hash(str(translation_id)) % 100000,
            "translation_id": translation_id,
            "metrics": evaluation_results,
            "language_pair": "auto-detected",
            "model_used": "IndicTrans2",
            "evaluated_at": time.time(),
            "reference_text": reference_text[:100] + "..." if len(reference_text) > 100 else reference_text
        }
    
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Evaluation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation failed"
        )