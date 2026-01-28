"""
Video localization routes
Handles video processing, subtitle generation, and audio replacement
"""
import os
import time
import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import SUPPORTED_LANGUAGES, get_settings
from app.services.video_processor import get_video_processor
from app.services.speech_engine import get_speech_engine
from app.services.nlp_engine import AdvancedNLPEngine
from app.utils.logger import app_logger

settings = get_settings()

router = APIRouter(prefix="/video", tags=["Video Localization"])

ALLOWED_VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB


@router.post("/localize")
async def video_localization(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    domain: Optional[str] = Form("general"),
    include_subtitles: bool = Form(True),
    include_dubbed_audio: bool = Form(False)
):
    """
    Complete video localization pipeline
    
    Steps:
    1. Extract audio from video
    2. Speech-to-Text (STT) with timestamps
    3. Translate text content
    4. Generate subtitles (.srt)
    5. Optionally generate dubbed audio and merge with video
    
    Output: Video with subtitles and/or dubbed audio in storage/outputs/
    """
    # Validate target language
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target language '{target_language}' not supported. Choose from: {list(SUPPORTED_LANGUAGES.keys())}"
        )
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Video format not supported. Allowed: {', '.join(ALLOWED_VIDEO_FORMATS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_VIDEO_SIZE // (1024*1024)} MB"
        )
    
    video_processor = get_video_processor()
    speech_engine = get_speech_engine()
    temp_files = []  # Track temp files for cleanup
    
    try:
        # Save video file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_video:
            temp_video.write(content)
            temp_video_path = temp_video.name
            temp_files.append(temp_video_path)
        
        app_logger.info(f"Starting video localization: {file.filename} → {target_language}")
        start_time = time.time()
        
        # Step 1: Validate video file
        validation = video_processor.validate_video_file(temp_video_path)
        if not validation["is_valid"]:
            raise ValueError(f"Invalid video file: {validation['error']}")
        
        # Step 2: Extract audio from video
        audio_extraction = video_processor.extract_audio_from_video(
            video_path=temp_video_path,
            output_format="wav"
        )
        
        if not audio_extraction["success"]:
            raise ValueError(f"Audio extraction failed: {audio_extraction.get('error', 'Unknown error')}")
        
        audio_path = audio_extraction["audio_path"]
        temp_files.append(audio_path)
        
        app_logger.info(f"Audio extracted successfully: {audio_path}")
        
        # Step 3: Speech-to-Text with timestamps
        stt_result = await speech_engine.speech_to_text_with_timestamps(
            audio_path=audio_path,
            language=None  # Auto-detect
        )
        
        source_text = stt_result["text"]
        detected_language = stt_result["language"]
        segments = stt_result["segments"]
        
        if not source_text.strip():
            raise ValueError("No speech detected in video audio")
        
        # Always use NLP engine for language detection to ensure accuracy
        app_logger.info("Using NLP engine for accurate language detection")
        nlp_engine = AdvancedNLPEngine()
        language_detection = nlp_engine.detect_language(source_text)
        detected_language = language_detection.get("detected_language", "en")
        detection_confidence = language_detection.get("confidence", 0.0)
        app_logger.info(f"NLP engine detected language: {detected_language} (confidence: {detection_confidence:.2f})")
        
        # Log the difference between STT and NLP detection
        stt_language = stt_result["language"]
        if stt_language != detected_language:
            app_logger.warning(f"Language detection mismatch: STT={stt_language}, NLP={detected_language}")
        
        app_logger.info(f"STT completed: '{source_text[:100]}...' (Language: {detected_language})")
        
        # Step 4: Translate content
        nlp_engine = AdvancedNLPEngine()
        
        # Translate full text
        translation_result = await nlp_engine.translate(
            text=source_text,
            source_language=detected_language,
            target_languages=[target_language],
            domain=domain
        )
        
        # Extract single language result
        target_result = translation_result["translations"][0]
        translated_text = target_result["translated_text"]
        confidence_score = target_result.get("confidence_score", target_result.get("confidence", 0.8))
        
        # Translate individual segments for subtitles
        translated_segments = []
        for i, segment in enumerate(segments):
            if segment["text"].strip():
                try:
                    # Translate each segment individually
                    segment_translation = await nlp_engine.translate(
                        text=segment["text"].strip(),
                        source_language=detected_language,
                        target_languages=[target_language],
                        domain=domain
                    )
                    
                    # Extract the translated text
                    if segment_translation["translations"] and len(segment_translation["translations"]) > 0:
                        segment_result = segment_translation["translations"][0]
                        translated_text = segment_result.get("translated_text", segment["text"].strip())
                    else:
                        translated_text = segment["text"].strip()  # Fallback to original
                    
                    translated_segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "original_text": segment["text"].strip(),
                        "translated_text": translated_text
                    })
                    
                    app_logger.debug(f"Segment {i+1} translated: '{segment['text'].strip()}' → '{translated_text}'")
                    
                except Exception as e:
                    app_logger.warning(f"Failed to translate segment {i+1}: {e}")
                    # Use original text as fallback
                    translated_segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "original_text": segment["text"].strip(),
                        "translated_text": segment["text"].strip()
                    })
        
        app_logger.info(f"Translation completed: {len(translated_segments)} segments translated")
        
        # Step 5: Generate output files
        timestamp = int(time.time())
        outputs = []
        
        # Generate subtitles if requested
        subtitle_path = None
        if include_subtitles:
            # Create SRT content with translated segments
            srt_content = []
            for i, segment in enumerate(translated_segments, 1):
                start_time_srt = _seconds_to_srt_time(segment["start"])
                end_time_srt = _seconds_to_srt_time(segment["end"])
                
                srt_content.extend([
                    str(i),
                    f"{start_time_srt} --> {end_time_srt}",
                    segment["translated_text"],
                    ""  # Empty line between segments
                ])
            
            # Save subtitle file
            subtitle_filename = f"video_subtitles_{target_language}_{timestamp}.srt"
            subtitle_path = os.path.join(settings.OUTPUT_DIR, subtitle_filename)
            
            # Ensure output directory exists
            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
            
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(srt_content))
            
            outputs.append({
                "type": "subtitles",
                "filename": subtitle_filename,
                "path": f"/storage/outputs/{subtitle_filename}",
                "language": target_language,
                "format": "srt"
            })
            
            app_logger.info(f"Subtitles saved: {subtitle_filename}")
        
        # Generate dubbed video if requested
        video_with_audio_path = None
        if include_dubbed_audio:
            # Generate translated audio using TTS
            tts_result = await speech_engine.text_to_speech(
                text=translated_text,
                language=target_language,
                output_format="wav"
            )
            
            dubbed_audio_path = tts_result["output_path"]
            temp_files.append(dubbed_audio_path)
            
            # Merge video with dubbed audio
            video_with_audio_filename = f"video_dubbed_{target_language}_{timestamp}.mp4"
            video_with_audio_path = os.path.join(settings.OUTPUT_DIR, video_with_audio_filename)
            
            audio_merge_result = video_processor.merge_video_with_audio(
                video_path=temp_video_path,
                audio_path=dubbed_audio_path,
                output_path=video_with_audio_path
            )
            
            if audio_merge_result["success"]:
                outputs.append({
                    "type": "dubbed_video",
                    "filename": video_with_audio_filename,
                    "path": f"/storage/outputs/{video_with_audio_filename}",
                    "language": target_language,
                    "format": "mp4"
                })
                app_logger.info(f"Dubbed video saved: {video_with_audio_filename}")
            else:
                app_logger.warning(f"Dubbed video generation failed: {audio_merge_result.get('error')}")
        
        # Generate video with burned-in subtitles if both subtitles and video are requested
        video_with_subs_path = None
        if include_subtitles and subtitle_path:
            video_with_subs_filename = f"video_with_subtitles_{target_language}_{timestamp}.mp4"
            video_with_subs_path = os.path.join(settings.OUTPUT_DIR, video_with_subs_filename)
            
            subs_merge_result = video_processor.merge_video_with_subtitles(
                video_path=temp_video_path,
                subtitle_path=subtitle_path,
                output_path=video_with_subs_path
            )
            
            if subs_merge_result["success"]:
                outputs.append({
                    "type": "video_with_subtitles",
                    "filename": video_with_subs_filename,
                    "path": f"/storage/outputs/{video_with_subs_filename}",
                    "language": target_language,
                    "format": "mp4"
                })
                app_logger.info(f"Video with subtitles saved: {video_with_subs_filename}")
        
        processing_time = time.time() - start_time
        
        # Clean up temporary files
        video_processor.cleanup_temp_files(temp_files)
        
        app_logger.info(f"Video localization completed in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "message": "Video localization completed successfully",
            "input_file": file.filename,
            "source_language": detected_language,
            "target_language": target_language,
            "domain": domain,
            "video_info": validation,
            "original_text": source_text[:200] + "..." if len(source_text) > 200 else source_text,
            "translated_text": translated_text[:200] + "..." if len(translated_text) > 200 else translated_text,
            "confidence_score": confidence_score,
            "segments_count": len(translated_segments),
            "processing_time_seconds": processing_time,
            "outputs": outputs
        }
        
    except Exception as e:
        app_logger.error(f"Video localization failed: {str(e)}")
        # Clean up temporary files on error
        if temp_files:
            video_processor.cleanup_temp_files(temp_files)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video localization failed: {str(e)}"
        )


@router.post("/extract-audio")
async def extract_audio_from_video(
    file: UploadFile = File(...),
    output_format: str = Form("wav")
):
    """
    Extract audio from video file
    
    Input: Video file (.mp4, .avi, .mov, etc.)
    Output: Audio file (.wav, .mp3, .aac) in storage/outputs/
    """
    # Validate output format
    if output_format not in ["wav", "mp3", "aac"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Output format must be 'wav', 'mp3', or 'aac'"
        )
    
    # Validate file extension
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_VIDEO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Video format not supported. Allowed: {', '.join(ALLOWED_VIDEO_FORMATS)}"
        )
    
    video_processor = get_video_processor()
    
    try:
        # Save video file temporarily
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_video:
            temp_video.write(content)
            temp_video_path = temp_video.name
        
        app_logger.info(f"Extracting audio from: {file.filename}")
        
        # Extract audio
        extraction_result = video_processor.extract_audio_from_video(
            video_path=temp_video_path,
            output_format=output_format
        )
        
        if not extraction_result["success"]:
            raise ValueError(extraction_result.get("error", "Audio extraction failed"))
        
        # Move extracted audio to outputs directory
        extracted_audio_path = extraction_result["audio_path"]
        output_filename = f"extracted_audio_{int(time.time())}.{output_format}"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Ensure output directory exists
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        # Copy to outputs directory
        import shutil
        shutil.copy2(extracted_audio_path, output_path)
        
        # Clean up temporary files
        os.unlink(temp_video_path)
        os.unlink(extracted_audio_path)
        
        app_logger.info(f"Audio extraction completed: {output_filename}")
        
        return {
            "status": "success",
            "message": "Audio extracted successfully",
            "input_file": file.filename,
            "output_file": output_filename,
            "output_path": f"/storage/outputs/{output_filename}",
            "format": output_format,
            "file_size_bytes": os.path.getsize(output_path)
        }
        
    except Exception as e:
        app_logger.error(f"Audio extraction failed: {str(e)}")
        # Clean up temporary files on error
        if 'temp_video_path' in locals() and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio extraction failed: {str(e)}"
        )


@router.get("/download/{filename}")
async def download_video_output(filename: str):
    """
    Download generated video or subtitle file
    """
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Determine media type based on file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        media_type = "video/mp4"
    elif file_ext == '.srt':
        media_type = "text/plain"
    elif file_ext in ['.wav', '.mp3', '.aac']:
        media_type = f"audio/{file_ext[1:]}"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"