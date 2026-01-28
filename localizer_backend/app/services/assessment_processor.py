"""
Assessment Processing Service
Handles JSON and CSV assessment file translation for educational content
"""
import os
import json
import csv
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import tempfile

from app.core.config import get_settings, SUPPORTED_LANGUAGES
from app.utils.logger import app_logger

settings = get_settings()


class AssessmentProcessor:
    """
    Production-ready assessment processor for educational content localization
    Handles JSON and CSV files with questions, options, and instructions
    """
    
    def __init__(self):
        self.supported_formats = ['.json', '.csv']
        self.text_fields = [
            'question', 'questions', 'text', 'content', 'prompt', 'description',
            'option', 'options', 'choice', 'choices', 'answer', 'answers',
            'instruction', 'instructions', 'explanation', 'feedback',
            'title', 'name', 'label', 'hint', 'note', 'comment'
        ]
        
        app_logger.info("Assessment Processor initialized")
    
    def process_json_assessment(
        self, 
        json_content: Dict, 
        target_language: str,
        nlp_engine: Any,
        domain: str = "education"
    ) -> Dict[str, Any]:
        """
        Process JSON assessment file and translate text fields
        
        Args:
            json_content: Parsed JSON content
            target_language: Target language code
            nlp_engine: NLP engine instance for translation
            domain: Domain context for translation
        
        Returns:
            Dict with translated JSON content
        """
        try:
            app_logger.info(f"Processing JSON assessment for translation to {target_language}")
            
            translated_content = self._translate_json_recursive(
                content=json_content,
                target_language=target_language,
                nlp_engine=nlp_engine,
                domain=domain
            )
            
            return {
                "success": True,
                "translated_content": translated_content,
                "message": "JSON assessment translated successfully"
            }
            
        except Exception as e:
            app_logger.error(f"JSON assessment processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "JSON assessment translation failed"
            }
    
    def process_csv_assessment(
        self, 
        csv_content: List[Dict], 
        target_language: str,
        nlp_engine: Any,
        domain: str = "education"
    ) -> Dict[str, Any]:
        """
        Process CSV assessment file and translate text fields
        
        Args:
            csv_content: Parsed CSV content as list of dictionaries
            target_language: Target language code
            nlp_engine: NLP engine instance for translation
            domain: Domain context for translation
        
        Returns:
            Dict with translated CSV content
        """
        try:
            app_logger.info(f"Processing CSV assessment for translation to {target_language}")
            
            translated_rows = []
            
            for row_idx, row in enumerate(csv_content):
                translated_row = {}
                
                for column, value in row.items():
                    if self._is_text_field(column) and isinstance(value, str) and value.strip():
                        # Translate text fields
                        translation_result = self._translate_text_sync(
                            text=value.strip(),
                            target_language=target_language,
                            nlp_engine=nlp_engine,
                            domain=domain
                        )
                        
                        translated_row[column] = translation_result.get("translated_text", value)
                        app_logger.debug(f"Row {row_idx}, Column '{column}': '{value[:50]}...' → '{translated_row[column][:50]}...'")
                    else:
                        # Keep non-text fields as-is
                        translated_row[column] = value
                
                translated_rows.append(translated_row)
            
            return {
                "success": True,
                "translated_content": translated_rows,
                "rows_processed": len(translated_rows),
                "message": "CSV assessment translated successfully"
            }
            
        except Exception as e:
            app_logger.error(f"CSV assessment processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "CSV assessment translation failed"
            }
    
    def _translate_json_recursive(
        self, 
        content: Any, 
        target_language: str, 
        nlp_engine: Any, 
        domain: str
    ) -> Any:
        """
        Recursively translate text fields in JSON structure
        """
        if isinstance(content, dict):
            translated_dict = {}
            for key, value in content.items():
                if self._is_text_field(key) and isinstance(value, str) and value.strip():
                    # Translate text fields
                    translation_result = self._translate_text_sync(
                        text=value.strip(),
                        target_language=target_language,
                        nlp_engine=nlp_engine,
                        domain=domain
                    )
                    translated_dict[key] = translation_result.get("translated_text", value)
                    app_logger.debug(f"Translated '{key}': '{value[:50]}...' → '{translated_dict[key][:50]}...'")
                elif isinstance(value, (dict, list)):
                    # Recursively process nested structures
                    translated_dict[key] = self._translate_json_recursive(
                        content=value,
                        target_language=target_language,
                        nlp_engine=nlp_engine,
                        domain=domain
                    )
                else:
                    # Keep non-text fields as-is
                    translated_dict[key] = value
            
            return translated_dict
            
        elif isinstance(content, list):
            translated_list = []
            for item in content:
                if isinstance(item, str) and item.strip():
                    # Translate string items in lists (like options)
                    translation_result = self._translate_text_sync(
                        text=item.strip(),
                        target_language=target_language,
                        nlp_engine=nlp_engine,
                        domain=domain
                    )
                    translated_list.append(translation_result.get("translated_text", item))
                elif isinstance(item, (dict, list)):
                    # Recursively process nested structures
                    translated_list.append(self._translate_json_recursive(
                        content=item,
                        target_language=target_language,
                        nlp_engine=nlp_engine,
                        domain=domain
                    ))
                else:
                    # Keep non-text items as-is
                    translated_list.append(item)
            
            return translated_list
        
        else:
            # Return primitive values as-is
            return content
    
    def _is_text_field(self, field_name: str) -> bool:
        """
        Check if a field name indicates it contains translatable text
        """
        field_lower = field_name.lower()
        
        # Direct matches
        if field_lower in self.text_fields:
            return True
        
        # Partial matches
        for text_field in self.text_fields:
            if text_field in field_lower or field_lower.endswith(text_field):
                return True
        
        # Skip ID, numeric, and metadata fields
        skip_patterns = ['id', 'index', 'number', 'count', 'score', 'point', 'weight', 
                        'correct', 'answer_key', 'type', 'format', 'version', 'created', 
                        'updated', 'author', 'timestamp', 'url', 'link', 'path']
        
        for pattern in skip_patterns:
            if pattern in field_lower:
                return False
        
        return False
    
    def _translate_text_sync(
        self, 
        text: str, 
        target_language: str, 
        nlp_engine: Any, 
        domain: str
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for text translation
        """
        try:
            # Use asyncio to run async translation function
            import asyncio
            
            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run translation
            if loop.is_running():
                # If loop is already running, create a new task
                future = asyncio.ensure_future(
                    nlp_engine.translate(
                        text=text,
                        source_language="auto",
                        target_languages=[target_language],
                        domain=domain
                    )
                )
                # Wait for completion
                while not future.done():
                    time.sleep(0.01)
                result = future.result()
            else:
                # Run in event loop
                result = loop.run_until_complete(
                    nlp_engine.translate(
                        text=text,
                        source_language="auto",
                        target_languages=[target_language],
                        domain=domain
                    )
                )
            
            # Extract single language result
            if "translations" in result and result["translations"]:
                return result["translations"][0]
            return result
            
        except Exception as e:
            app_logger.warning(f"Translation failed for text '{text[:50]}...': {e}")
            return {"translated_text": text, "confidence_score": 0.0}
    
    def save_translated_assessment(
        self, 
        translated_content: Any, 
        original_format: str, 
        target_language: str, 
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save translated assessment to storage/outputs/
        
        Args:
            translated_content: Translated assessment content
            original_format: Original file format (json or csv)
            target_language: Target language code
            output_filename: Optional custom filename
        
        Returns:
            Dict with save results and file information
        """
        try:
            # Generate filename if not provided
            if not output_filename:
                timestamp = int(time.time())
                output_filename = f"assessment_{target_language}_{timestamp}.{original_format}"
            
            output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
            
            # Ensure output directory exists
            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
            
            if original_format == 'json':
                # Save as JSON file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(translated_content, f, ensure_ascii=False, indent=2)
                    
            elif original_format == 'csv':
                # Save as CSV file
                if translated_content and isinstance(translated_content, list):
                    fieldnames = list(translated_content[0].keys()) if translated_content else []
                    
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(translated_content)
                else:
                    raise ValueError("Invalid CSV content format")
            
            file_size = os.path.getsize(output_path)
            app_logger.info(f"Translated assessment saved: {output_filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "output_filename": output_filename,
                "output_path": f"/storage/outputs/{output_filename}",
                "file_size_bytes": file_size,
                "format": original_format,
                "message": "Translated assessment saved successfully"
            }
            
        except Exception as e:
            app_logger.error(f"Failed to save translated assessment: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to save translated assessment"
            }
    
    def validate_assessment_file(self, file_path: str, file_format: str) -> Dict[str, Any]:
        """
        Validate assessment file format and content
        
        Args:
            file_path: Path to assessment file
            file_format: Expected format (json or csv)
        
        Returns:
            Dict with validation results
        """
        try:
            if not os.path.exists(file_path):
                return {"is_valid": False, "error": "File does not exist"}
            
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                return {"is_valid": False, "error": "File too large (max 50MB)"}
            
            if file_format == 'json':
                # Validate JSON structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                
                # Count text fields
                text_fields_count = self._count_text_fields_json(content)
                
                return {
                    "is_valid": True,
                    "format": "json",
                    "file_size_bytes": file_size,
                    "estimated_text_fields": text_fields_count,
                    "content_type": type(content).__name__
                }
                
            elif file_format == 'csv':
                # Validate CSV structure
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Try to read first few lines
                    sample = f.read(1024)
                    f.seek(0)
                    
                    # Detect delimiter
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    first_row = next(reader, None)
                    
                    if not first_row:
                        return {"is_valid": False, "error": "Empty CSV file"}
                    
                    # Count rows and text columns
                    f.seek(0)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    row_count = sum(1 for _ in reader)
                    
                    text_columns = [col for col in first_row.keys() if self._is_text_field(col)]
                
                return {
                    "is_valid": True,
                    "format": "csv",
                    "file_size_bytes": file_size,
                    "row_count": row_count,
                    "column_count": len(first_row.keys()),
                    "text_columns": text_columns,
                    "estimated_text_fields": len(text_columns) * row_count
                }
            
            else:
                return {"is_valid": False, "error": f"Unsupported format: {file_format}"}
                
        except Exception as e:
            return {"is_valid": False, "error": str(e)}
    
    def _count_text_fields_json(self, content: Any) -> int:
        """Count estimated text fields in JSON content"""
        count = 0
        
        if isinstance(content, dict):
            for key, value in content.items():
                if self._is_text_field(key) and isinstance(value, str) and value.strip():
                    count += 1
                elif isinstance(value, (dict, list)):
                    count += self._count_text_fields_json(value)
                    
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str) and item.strip():
                    count += 1
                elif isinstance(item, (dict, list)):
                    count += self._count_text_fields_json(item)
        
        return count


# Global instance
assessment_processor = AssessmentProcessor()


def get_assessment_processor() -> AssessmentProcessor:
    """Get the global assessment processor instance"""
    return assessment_processor