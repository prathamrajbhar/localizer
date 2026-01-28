"""
File management utilities
"""
import os
import uuid
import shutil
import json
from pathlib import Path
from typing import Optional, Dict
from fastapi import UploadFile
from app.core.config import get_settings
from app.utils.logger import app_logger

settings = get_settings()


class FileManager:
    """Manages file operations for uploads and outputs"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.output_dir = Path(settings.OUTPUT_DIR)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure storage directories exist"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        app_logger.info(f"Storage directories initialized: {self.upload_dir}, {self.output_dir}")
    
    async def save_upload(
        self, 
        file: UploadFile, 
        file_id: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Save uploaded file to disk
        
        Args:
            file: UploadFile object
            file_id: Optional file ID, generates UUID if not provided
        
        Returns:
            Dict with file_path, filename, and file_id
        """
        if file_id is None:
            file_id = str(uuid.uuid4())
        
        # Create directory for this file
        file_dir = self.upload_dir / str(file_id)
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = file_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Save metadata
        metadata = {
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": len(content)
        }
        metadata_path = file_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        app_logger.info(f"File saved: {file_path}")
        
        return {
            "file_path": str(file_path),
            "filename": file.filename,
            "file_id": str(file_id),
            "size": len(content)
        }
    
    def create_output_dir(self, job_id: int) -> Path:
        """Create output directory for a job"""
        output_path = self.output_dir / str(job_id)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def save_translation(
        self, 
        job_id: int, 
        language: str, 
        translation: Dict
    ) -> str:
        """
        Save translation output as JSON
        
        Args:
            job_id: Job ID
            language: Target language code
            translation: Translation data
        
        Returns:
            Path to saved file
        """
        output_dir = self.create_output_dir(job_id)
        output_file = output_dir / f"translation_{language}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translation, f, indent=2, ensure_ascii=False)
        
        app_logger.info(f"Translation saved: {output_file}")
        return str(output_file)
    
    def save_audio(self, job_id: int, language: str, audio_data: bytes) -> str:
        """
        Save TTS audio output
        
        Args:
            job_id: Job ID
            language: Language code
            audio_data: Audio bytes
        
        Returns:
            Path to saved audio file
        """
        output_dir = self.create_output_dir(job_id)
        audio_file = output_dir / f"tts_{language}.mp3"
        
        with open(audio_file, "wb") as f:
            f.write(audio_data)
        
        app_logger.info(f"Audio saved: {audio_file}")
        return str(audio_file)
    
    def save_transcript(self, job_id: int, transcript: str) -> str:
        """
        Save STT transcript
        
        Args:
            job_id: Job ID
            transcript: Transcribed text
        
        Returns:
            Path to saved transcript file
        """
        output_dir = self.create_output_dir(job_id)
        transcript_file = output_dir / "transcript.txt"
        
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcript)
        
        app_logger.info(f"Transcript saved: {transcript_file}")
        return str(transcript_file)
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            path = Path(file_path)
            if path.is_file():
                path.unlink()
                app_logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            app_logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def delete_directory(self, dir_path: str) -> bool:
        """Delete a directory and its contents"""
        try:
            path = Path(dir_path)
            if path.is_dir():
                shutil.rmtree(path)
                app_logger.info(f"Directory deleted: {dir_path}")
                return True
            return False
        except Exception as e:
            app_logger.error(f"Error deleting directory {dir_path}: {e}")
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return Path(file_path).stat().st_size
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()


# Global file manager instance
file_manager = FileManager()

