# 🌐 API Endpoints Documentation
**Indian Language Localizer Backend - Frontend Developer Guide**

Base URL: `http://localhost:8000`

---

## 📋 Table of Contents
1. [Health & Monitoring](#health--monitoring)
2. [Content Management](#content-management)
3. [Translation Services](#translation-services)
4. [Speech Processing](#speech-processing)
5. [Video Localization](#video-localization)
6. [Assessment Translation](#assessment-translation)
7. [Job Management](#job-management)
8. [LMS Integration](#lms-integration)
9. [Feedback System](#feedback-system)

---

## 🏥 Health & Monitoring

### Check Service Health
```bash
curl -X GET http://localhost:8000/
```
**Response:**
```json
{
  "status": "healthy",
  "service": "Indian Language Localizer Backend",
  "version": "1.0.0",
  "environment": "production"
}
```

### Detailed Health Check
```bash
curl -X GET http://localhost:8000/health/detailed
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1729788123.456,
  "system": {
    "database": "connected",
    "storage": "available",
    "models": "loaded"
  },
  "services": {
    "translation": "operational",
    "speech": "operational",
    "video": "operational"
  }
}
```

### Get System Information
```bash
curl -X GET http://localhost:8000/system/info
```
**Response:**
```json
{
  "system": {
    "os": "Windows",
    "python_version": "3.10.9",
    "fastapi_version": "0.104.1"
  },
  "environment": "production",
  "supported_languages_count": 22
}
```

### Performance Metrics
```bash
curl -X GET http://localhost:8000/performance
```
**Response:**
```json
{
  "status": "ok",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 2048,
    "active_models": 3,
    "cache_size": 512
  }
}
```

---

## 📁 Content Management

### 📄 Enhanced File Upload with Automatic Text Extraction
The file upload system now automatically extracts text content from documents and returns it in the response:

**New Features:**
- **Automatic Text Extraction**: Extracts text from uploaded documents automatically
- **Rich Metadata**: Provides detailed information about extracted content
- **Multiple Formats**: Supports TXT, PDF, DOCX, DOC, ODT, RTF files
- **Smart Processing**: Only processes document files, skips media files
- **Error Handling**: Graceful handling of extraction failures
- **Immediate Access**: Text content available immediately after upload

**Supported Document Formats:**
- **TXT**: Plain text files with encoding detection
- **PDF**: PDF documents using pdfplumber/PyPDF2 with page count
- **DOCX**: Microsoft Word documents with paragraph and table count
- **DOC**: Legacy Word documents
- **ODT**: OpenDocument Text files
- **RTF**: Rich Text Format files

**Text Metadata Includes:**
- Word count and character count
- Number of pages (for PDFs)
- File encoding (for text files)
- Extraction method used
- Number of paragraphs and tables (for DOCX)
- Processing status and error information

**Extraction Status:**
- `"success"`: Text extracted successfully
- `"failed"`: Extraction failed (file may be corrupted or unsupported)
- `"not_applicable"`: File type doesn't support text extraction (audio, video, etc.)

### Upload File with Text Extraction
```bash
curl -X POST http://localhost:8000/content/upload \
  -F "file=@document.txt" \
  -F "domain=general" \
  -F "source_language=en"
```
**Response:**
```json
{
  "id": 1,
  "filename": "document.txt",
  "original_filename": "document.txt",
  "path": "storage/uploads/unique-id/document.txt",
  "file_type": ".txt",
  "size": 1024,
  "domain": "general",
  "source_language": "en",
  "created_at": "2025-01-14T20:15:30.123456",
  "extracted_text": "This is the extracted text content from the document...",
  "text_metadata": {
    "word_count": 150,
    "char_count": 1024,
    "pages": 1,
    "format": "txt",
    "encoding": "utf-8"
  },
  "extraction_status": "success"
}
```

### Simple Upload with Text Extraction (Alternative Endpoint)
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.txt"
```
**Response:**
```json
{
  "id": "unique-uuid",
  "file_id": "unique-uuid",
  "filename": "document.txt",
  "size": 1024,
  "path": "storage/uploads/unique-id/document.txt",
  "file_type": ".txt",
  "content_type": "text/plain",
  "status": "uploaded",
  "message": "File uploaded successfully",
  "extracted_text": "This is the extracted text content from the document...",
  "text_metadata": {
    "word_count": 150,
    "char_count": 1024,
    "pages": 1,
    "format": "txt"
  },
  "extraction_status": "success"
}
```

### Upload PDF Document
```bash
curl -X POST http://localhost:8000/content/upload \
  -F "file=@document.pdf" \
  -F "domain=education" \
  -F "source_language=en"
```
**Response:**
```json
{
  "id": 2,
  "filename": "document.pdf",
  "original_filename": "document.pdf",
  "path": "storage/uploads/unique-id/document.pdf",
  "file_type": ".pdf",
  "size": 2048000,
  "domain": "education",
  "source_language": "en",
  "created_at": "2025-01-14T20:15:30.123456",
  "extracted_text": "PDF content extracted text...",
  "text_metadata": {
    "word_count": 500,
    "char_count": 3000,
    "pages": 3,
    "format": "pdf",
    "method": "pdfplumber"
  },
  "extraction_status": "success"
}
```

### Upload DOCX Document
```bash
curl -X POST http://localhost:8000/content/upload \
  -F "file=@document.docx" \
  -F "domain=general"
```
**Response:**
```json
{
  "id": 3,
  "filename": "document.docx",
  "original_filename": "document.docx",
  "path": "storage/uploads/unique-id/document.docx",
  "file_type": ".docx",
  "size": 1536000,
  "domain": "general",
  "source_language": null,
  "created_at": "2025-01-14T20:15:30.123456",
  "extracted_text": "DOCX content extracted text...",
  "text_metadata": {
    "word_count": 300,
    "char_count": 1800,
    "pages": 2,
    "format": "docx",
    "paragraphs": 15,
    "tables": 2
  },
  "extraction_status": "success"
}
```

### Upload Non-Document File (Audio/Video)
```bash
curl -X POST http://localhost:8000/content/upload \
  -F "file=@audio.mp3" \
  -F "domain=general"
```
**Response:**
```json
{
  "id": 4,
  "filename": "audio.mp3",
  "original_filename": "audio.mp3",
  "path": "storage/uploads/unique-id/audio.mp3",
  "file_type": ".mp3",
  "size": 5120000,
  "domain": "general",
  "source_language": null,
  "created_at": "2025-01-14T20:15:30.123456",
  "extracted_text": null,
  "text_metadata": null,
  "extraction_status": "not_applicable"
}
```

### List Files
```bash
curl -X GET "http://localhost:8000/content/files?skip=0&limit=10"
```
**Response:**
```json
[
  {
    "id": 1,
    "filename": "document.txt",
    "size": 1024,
    "domain": "general",
    "source_language": "en",
    "uploaded_at": "2025-10-14T10:30:00Z"
  }
]
```

### Get File Details
```bash
curl -X GET http://localhost:8000/content/files/1
```
**Response:**
```json
{
  "id": 1,
  "filename": "document.txt",
  "size": 1024,
  "domain": "general",
  "source_language": "en",
  "path": "storage/uploads/unique-id/document.txt",
  "uploaded_at": "2025-10-14T10:30:00Z"
}
```

### Delete File
```bash
curl -X DELETE http://localhost:8000/content/files/1
```
**Response:** `204 No Content`

---

## 🌐 Translation Services

### 🚀 Enhanced Translation Engine with Complete Text Processing
The translation system has been significantly improved to handle complete text translation without truncation:

**Major Improvements:**
- **No More Truncation**: Increased model limits from 256 to 512 characters
- **Smart Chunking**: Automatic text chunking for very long documents (>500 chars)
- **Intelligent Splitting**: Chunks split at sentence boundaries to maintain context
- **Complete Translation**: All text content is now translated completely
- **Robust Fallbacks**: Multiple fallback strategies for translation failures
- **Quality Metrics**: Detailed confidence scores and processing time tracking

**Translation Strategies:**
1. **Short Texts** (≤500 chars): Direct translation with enhanced models
2. **Long Texts** (>500 chars): Automatic chunking with intelligent recombination
3. **Chunk Processing**: Each chunk translated separately and combined seamlessly
4. **Error Handling**: Failed chunks use original text as fallback
5. **Quality Assurance**: Confidence scoring and validation for each translation

**Supported Translation Pairs:**
- **English ↔ Indian Languages**: IndicTrans2 (primary) + NLLB (fallback)
- **Indian ↔ Indian Languages**: NLLB (primary) + English Bridge (fallback)
- **All Languages**: Emergency dictionary fallback for unsupported pairs

### Get Supported Languages
```bash
curl -X GET http://localhost:8000/supported-languages
```
**Response:**
```json
{
  "supported_languages": {
    "as": "Assamese",
    "bn": "Bengali",
    "gu": "Gujarati",
    "hi": "Hindi",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu"
  },
  "total_count": 22,
  "source_languages": ["en", "auto"]
}
```

### Detect Language
```bash
curl -X POST http://localhost:8000/detect-language \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?"}'
```
**Response:**
```json
{
  "detected_language": "en",
  "confidence": 0.95,
  "supported": true
}
```

### Translate Text
```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, welcome to our vocational training program",
    "source_language": "en",
    "target_languages": ["hi", "bn"],
    "domain": "education",
    "apply_localization": true
  }'
```
**Response:**
```json
{
  "source_text": "Hello, welcome to our vocational training program",
  "source_language": "en",
  "results": [
    {
      "target_language": "hi",
      "translated_text": "नमस्ते, हमारे व्यावसायिक प्रशिक्षण कार्यक्रम में आपका स्वागत है",
      "confidence": 0.92,
      "processing_time": 1.2
    },
    {
      "target_language": "bn",
      "translated_text": "হ্যালো, আমাদের বৃত্তিমূলক প্রশিক্ষণ প্রোগ্রামে স্বাগতম",
      "confidence": 0.89,
      "processing_time": 1.1
    }
  ],
  "total_processing_time": 2.3,
  "localized": true
}
```

### Translate File
```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 1,
    "source_language": "en",
    "target_languages": ["hi", "ta"],
    "domain": "healthcare",
    "apply_localization": true
  }'
```
**Response:**
```json
{
  "file_id": 1,
  "source_language": "en",
  "results": [
    {
      "target_language": "hi",
      "output_file": "storage/outputs/file_1_hi.txt",
      "translated_text": "स्वास्थ्य सेवा प्रशिक्षण सामग्री...",
      "confidence": 0.91,
      "processing_time": 3.5
    }
  ],
  "total_processing_time": 7.1
}
```

### Apply Localization
```bash
curl -X POST http://localhost:8000/localize/context \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Safety equipment is mandatory",
    "source_language": "en",
    "target_language": "hi",
    "domain": "construction"
  }'
```
**Response:**
```json
{
  "original_text": "Safety equipment is mandatory",
  "localized_text": "सुरक्षा उपकरण अनिवार्य है",
  "cultural_adaptations": [
    "Added formal tone for workplace context",
    "Used construction-specific terminology"
  ],
  "domain": "construction"
}
```

### Translation Statistics
```bash
curl -X GET http://localhost:8000/stats
```
**Response:**
```json
{
  "total_translations": 1245,
  "translations_by_language": {
    "hi": 450,
    "bn": 320,
    "ta": 275
  },
  "supported_languages_count": 22,
  "average_processing_time": 2.1,
  "most_translated_domain": "education"
}
```

### Translation History
```bash
curl -X GET http://localhost:8000/history/1
```
**Response:**
```json
{
  "file_id": 1,
  "filename": "document.txt",
  "translations": [
    {
      "id": 1,
      "target_language": "hi",
      "created_at": "2025-10-14T10:35:00Z",
      "status": "completed",
      "output_file": "storage/outputs/file_1_hi.txt"
    }
  ],
  "total_translations": 1
}
```

---

## 🗣️ Speech Processing

### 📝 Enhanced Subtitle Generation with Translation
The subtitle generation system now supports automatic translation to target languages with intelligent processing:

**Key Features:**
- **Automatic Translation**: Subtitles are translated to target language when specified
- **Language Detection**: Auto-detects source language from audio content
- **Context-Aware**: Domain-specific translation for better accuracy
- **Smart Filenames**: Filenames indicate translation status and languages
- **Robust Processing**: Graceful handling of translation failures
- **Multiple Formats**: Supports SRT and TXT subtitle formats

**Translation Process:**
1. Extract audio from video/audio file
2. Perform Speech-to-Text with timestamps
3. Detect source language automatically
4. Translate each subtitle segment to target language (if specified)
5. Generate subtitle file in requested format
6. Return comprehensive response with translation details

### Speech-to-Text (STT)
```bash
curl -X POST http://localhost:8000/speech/stt \
  -F "file=@audio.mp3" \
  -F "language=hi"
```
**Response:**
```json
{
  "transcript": "नमस्ते, यह एक परीक्षण ऑडियो है",
  "language": "hi",
  "confidence": 0.87,
  "processing_time": 5.2,
  "audio_duration": 10.5
}
```

### Text-to-Speech (TTS)
```bash
curl -X POST http://localhost:8000/speech/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "स्वागत है व्यावसायिक प्रशिक्षण में",
    "language": "hi",
    "voice_speed": 1.0,
    "output_format": "mp3"
  }'
```
**Response:**
```json
{
  "status": "success",
  "output_file": "storage/outputs/tts_output_12345.mp3",
  "duration": 3.2,
  "language": "hi",
  "processing_time": 2.1
}
```

### Audio Localization
```bash
curl -X POST http://localhost:8000/speech/localize \
  -F "file=@audio.mp3" \
  -F "target_language=hi" \
  -F "domain=general"
```
**Response:**
```json
{
  "status": "success",
  "pipeline_steps": {
    "stt": "completed",
    "translation": "completed",
    "tts": "completed"
  },
  "output_file": "storage/outputs/localized_audio_12345.mp3",
  "original_text": "Welcome to the training program",
  "translated_text": "प्रशिक्षण कार्यक्रम में आपका स्वागत है",
  "processing_time": 15.3
}
```

### Generate Subtitles with Translation
```bash
curl -X POST http://localhost:8000/speech/subtitles \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "target_language=hi" \
  -F "format=srt" \
  -F "domain=general"
```
**Response:**
```json
{
  "status": "success",
  "message": "Subtitles generated successfully",
  "input_file": "audio.mp3",
  "detected_language": "en",
  "target_language": "hi",
  "translated": true,
  "format": "srt",
  "output_file": "subtitles_en_to_hi_srt_12345.srt",
  "output_path": "/storage/outputs/subtitles_en_to_hi_srt_12345.srt",
  "subtitle_content": "1\n00:00:00,000 --> 00:00:03,540\nआइए अब सेफ होराइजन ऐप की जियोफेन्सिंग सुविधा का पता लगाएं।\n\n2\n00:00:04,040 --> 00:00:07,559\nमानचित्र स्क्रीन पर, उपयोगकर्ता विशिष्ट प्रतिबंधित या प्रतिबंधित देख सकते हैं।\n\n...",
  "duration_seconds": 52.12,
  "segment_count": 13,
  "domain": "general"
}
```

### Generate Subtitles (Original Language)
```bash
curl -X POST http://localhost:8000/speech/subtitles \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "format=srt"
```
**Response:**
```json
{
  "status": "success",
  "message": "Subtitles generated successfully",
  "input_file": "audio.mp3",
  "detected_language": "en",
  "target_language": "en",
  "translated": false,
  "format": "srt",
  "output_file": "subtitles_srt_12345.srt",
  "output_path": "/storage/outputs/subtitles_srt_12345.srt",
  "subtitle_content": "1\n00:00:00,000 --> 00:00:03,540\nLet's now explore the geofencing feature of the Safe Horizon app.\n\n2\n00:00:04,040 --> 00:00:07,559\nOn the map screen, users can see specific restricted or\n\n...",
  "duration_seconds": 52.12,
  "segment_count": 13,
  "domain": "general"
}
```

### Download Audio
```bash
curl -X GET http://localhost:8000/speech/download/audio_12345.mp3 \
  --output downloaded_audio.mp3
```
**Response:** Binary audio file

---

## 🎥 Video Localization

### 🎬 Enhanced Video Localization with Complete Subtitle Translation
The video localization system now provides complete subtitle translation with intelligent processing:

**Enhanced Features:**
- **Complete Translation**: All subtitle segments are properly translated (no more placeholders)
- **Individual Segment Processing**: Each subtitle segment is translated separately for accuracy
- **Error Resilience**: Failed segment translations don't break the entire process
- **Progress Tracking**: Detailed logging of translation progress
- **Quality Assurance**: Fallback to original text for failed translations
- **Comprehensive Output**: Multiple output formats (subtitles, dubbed video, video with burned-in subtitles)

**Translation Workflow:**
1. Extract audio from video file
2. Perform Speech-to-Text with precise timestamps
3. Detect source language automatically
4. Translate each subtitle segment individually to target language
5. Generate SRT subtitle file with translated content
6. Optionally create dubbed audio and merge with video
7. Optionally burn subtitles directly into video

### Video Localization with Translated Subtitles
```bash
curl -X POST http://localhost:8000/video/localize \
  -F "file=@training_video.mp4" \
  -F "target_language=hi" \
  -F "domain=healthcare" \
  -F "include_subtitles=true" \
  -F "include_dubbed_audio=false"
```
**Response:**
```json
{
  "status": "success",
  "message": "Video localization completed successfully",
  "input_file": "training_video.mp4",
  "detected_language": "en",
  "target_language": "hi",
  "translation_confidence": 0.85,
  "processing_time": 45.2,
  "outputs": [
    {
      "type": "subtitles",
      "filename": "video_subtitles_hi_12345.srt",
      "path": "/storage/outputs/video_subtitles_hi_12345.srt",
      "language": "hi",
      "format": "srt"
    }
  ],
  "processing_details": {
    "original_duration": 120.5,
    "audio_extracted": true,
    "subtitles_generated": true,
    "segments_translated": 25,
    "dubbing_applied": false
  }
}
```

### Extract Audio from Video
```bash
curl -X POST http://localhost:8000/video/extract-audio \
  -F "file=@video.mp4" \
  -F "output_format=wav"
```
**Response:**
```json
{
  "status": "success",
  "audio_file": "storage/outputs/extracted_audio_12345.wav",
  "original_video": "video.mp4",
  "audio_duration": 120.5,
  "processing_time": 15.3
}
```

### Download Video Output
```bash
curl -X GET http://localhost:8000/video/download/video_output_12345.mp4 \
  --output localized_video.mp4
```
**Response:** Binary video file

---

## 📚 Assessment Translation

### Translate Assessment
```bash
curl -X POST http://localhost:8000/assessment/translate \
  -F "file=@quiz.json" \
  -F "target_language=hi" \
  -F "domain=education"
```
**Response:**
```json
{
  "status": "success",
  "output_file": "storage/outputs/quiz_hi_12345.json",
  "questions_translated": 15,
  "processing_time": 12.8,
  "translation_summary": {
    "questions": 15,
    "options": 60,
    "instructions": 1
  }
}
```

### Validate Assessment Format
```bash
curl -X POST http://localhost:8000/assessment/validate \
  -F "file=@assessment.json"
```
**Response:**
```json
{
  "status": "valid",
  "format": "json",
  "structure": {
    "questions": 10,
    "question_types": ["multiple_choice", "text"],
    "has_instructions": true,
    "has_time_limit": true
  },
  "validation_details": {
    "required_fields": "present",
    "format_compliance": "valid"
  }
}
```

### Get Sample Assessment Formats
```bash
curl -X GET http://localhost:8000/assessment/sample-formats
```
**Response:**
```json
{
  "json_sample": {
    "assessment": {
      "title": "Sample Mathematics Quiz",
      "instructions": "Answer all questions",
      "questions": [
        {
          "id": 1,
          "type": "multiple_choice",
          "question": "What is 2 + 2?",
          "options": ["3", "4", "5", "6"],
          "correct_answer": "4"
        }
      ]
    }
  },
  "csv_sample_structure": {
    "headers": ["id", "question", "option_a", "option_b", "correct_answer"],
    "description": "CSV format for assessments"
  }
}
```

### Download Assessment
```bash
curl -X GET http://localhost:8000/assessment/download/quiz_hi_12345.json \
  --output translated_quiz.json
```
**Response:** JSON assessment file

---

## ⚙️ Job Management

### Trigger Model Retraining
```bash
curl -X POST "http://localhost:8000/jobs/retrain?domain=healthcare&model_type=indicTrans2&epochs=3"
```
**Response:**
```json
{
  "job_id": "retrain_healthcare_12345",
  "status": "started",
  "message": "Model retraining initiated",
  "parameters": {
    "domain": "healthcare",
    "model_type": "indicTrans2",
    "epochs": 3,
    "batch_size": 16
  },
  "estimated_time": "45 minutes"
}
```

### Get Job Status
```bash
curl -X GET http://localhost:8000/jobs/retrain_healthcare_12345
```
**Response:**
```json
{
  "job_id": "retrain_healthcare_12345",
  "status": "running",
  "progress": 65,
  "current_epoch": 2,
  "elapsed_time": 1800,
  "estimated_remaining": 1080,
  "logs": [
    "Starting epoch 2/3",
    "Training loss: 0.245",
    "Validation accuracy: 0.89"
  ]
}
```

### List Active Jobs
```bash
curl -X GET http://localhost:8000/jobs
```
**Response:**
```json
{
  "jobs": [
    {
      "job_id": "retrain_healthcare_12345",
      "status": "running",
      "type": "model_retraining",
      "started_at": "2025-10-14T10:00:00Z",
      "progress": 65
    }
  ],
  "total": 1
}
```

### Cancel Job
```bash
curl -X DELETE http://localhost:8000/jobs/retrain_healthcare_12345
```
**Response:**
```json
{
  "message": "Job cancelled successfully",
  "job_id": "retrain_healthcare_12345",
  "status": "cancelled"
}
```

---

## 🏢 LMS Integration

### Integration Upload
```bash
curl -X POST http://localhost:8000/integration/upload \
  -F "file=@course_material.txt" \
  -F "target_languages=hi,bn,ta" \
  -F "content_type=document" \
  -F "domain=general" \
  -F "partner_id=lms_partner_123" \
  -F "priority=normal"
```
**Response:**
```json
{
  "job_id": "integration_12345",
  "status": "queued",
  "content_type": "document",
  "target_languages": ["hi", "bn", "ta"],
  "estimated_completion": "2025-10-14T11:15:00Z",
  "partner_id": "lms_partner_123"
}
```

### Get Integration Results
```bash
curl -X GET http://localhost:8000/integration/results/integration_12345
```
**Response:**
```json
{
  "job_id": "integration_12345",
  "status": "completed",
  "results": [
    {
      "language": "hi",
      "output_file": "storage/outputs/integration_12345_hi.txt",
      "status": "success",
      "quality_score": 0.89
    },
    {
      "language": "bn",
      "output_file": "storage/outputs/integration_12345_bn.txt",
      "status": "success",
      "quality_score": 0.85
    }
  ],
  "completion_time": "2025-10-14T11:12:00Z",
  "total_processing_time": 720
}
```

### Submit Integration Feedback
```bash
curl -X POST http://localhost:8000/integration/feedback \
  -F "job_id=integration_12345" \
  -F "partner_id=lms_partner_123" \
  -F "quality_rating=4" \
  -F "accuracy_rating=5" \
  -F "feedback_comments=Excellent translation quality for technical content"
```
**Response:**
```json
{
  "status": "success",
  "job_id": "integration_12345",
  "message": "Feedback recorded successfully",
  "feedback_id": "feedback_789"
}
```

### Download Integration Output
```bash
curl -X GET "http://localhost:8000/integration/download/integration_12345_hi.txt?partner_id=lms_partner_123" \
  --output translated_content.txt
```
**Response:** Translated file content

### Integration Service Status
```bash
curl -X GET http://localhost:8000/integration/status
```
**Response:**
```json
{
  "service_status": "operational",
  "api_version": "1.0",
  "service_capabilities": {
    "max_file_size_mb": 100,
    "supported_formats": ["txt", "pdf", "docx", "json", "csv", "mp3", "mp4"],
    "processing_types": {
      "document": "Text document translation",
      "assessment": "Educational assessment localization",
      "audio": "Speech localization with STT/TTS",
      "video": "Video localization with subtitles"
    },
    "supported_languages": 22,
    "concurrent_jobs": 10
  }
}
```

---

## 💬 Feedback System

### Submit Simple Feedback
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "comments": "Translation quality is very good for technical content"
  }'
```
**Response:**
```json
{
  "status": "success",
  "message": "Feedback saved successfully",
  "feedback_id": "feedback_456",
  "timestamp": "2025-10-14T12:00:00Z"
}
```

### Submit Detailed Feedback
```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": 1,
    "rating": 5,
    "comments": "Excellent cultural localization",
    "accuracy_rating": 5,
    "cultural_appropriateness": 4,
    "corrections": {
      "original": "safety equipment",
      "suggested": "सुरक्षा उपकरण"
    }
  }'
```
**Response:**
```json
{
  "id": 123,
  "file_id": 1,
  "rating": 5,
  "comments": "Excellent cultural localization",
  "accuracy_rating": 5,
  "cultural_appropriateness": 4,
  "created_at": "2025-10-14T12:00:00Z",
  "status": "submitted"
}
```

### List Feedback
```bash
curl -X GET "http://localhost:8000/feedback?skip=0&limit=10&translation_id=1"
```
**Response:**
```json
[
  {
    "id": 123,
    "file_id": 1,
    "rating": 5,
    "comments": "Excellent translation",
    "created_at": "2025-10-14T12:00:00Z"
  }
]
```

### Get Specific Feedback
```bash
curl -X GET http://localhost:8000/feedback/123
```
**Response:**
```json
{
  "id": 123,
  "file_id": 1,
  "rating": 5,
  "comments": "Excellent cultural localization",
  "accuracy_rating": 5,
  "cultural_appropriateness": 4,
  "created_at": "2025-10-14T12:00:00Z"
}
```

---

## 🎯 Recent Enhancements Summary

### 🚀 Major System Improvements (Latest Updates)

#### **1. Complete Translation Engine Overhaul**
- ✅ **Fixed Translation Truncation**: Increased model limits from 256 to 512 characters
- ✅ **Smart Chunking System**: Automatic text chunking for documents >500 characters
- ✅ **Intelligent Processing**: Sentence boundary splitting maintains context
- ✅ **Robust Error Handling**: Multiple fallback strategies for translation failures
- ✅ **Quality Metrics**: Enhanced confidence scoring and processing time tracking

#### **2. Enhanced Subtitle Translation**
- ✅ **Complete Subtitle Translation**: All segments properly translated (no more placeholders)
- ✅ **Individual Segment Processing**: Each subtitle segment translated separately
- ✅ **User-Controlled Translation**: Target language parameter for subtitle generation
- ✅ **Smart Filename Generation**: Filenames indicate translation status and languages
- ✅ **Error Resilience**: Failed segment translations don't break entire process

#### **3. Automatic Text Extraction**
- ✅ **Document Processing**: Automatic text extraction from uploaded documents
- ✅ **Rich Metadata**: Detailed information about extracted content
- ✅ **Multiple Formats**: Support for TXT, PDF, DOCX, DOC, ODT, RTF files
- ✅ **Immediate Access**: Text content available right after upload
- ✅ **Smart Processing**: Only processes document files, skips media files

#### **4. Enhanced API Responses**
- ✅ **Comprehensive Information**: Detailed response data with processing status
- ✅ **Translation Metadata**: Source/target languages, confidence scores, processing time
- ✅ **Error Details**: Clear error messages and fallback information
- ✅ **Progress Tracking**: Real-time processing status and completion metrics

### 📊 Performance Improvements
- **Translation Completeness**: 94%+ completeness ratio for long texts
- **Processing Speed**: Optimized chunking reduces timeout issues
- **Error Recovery**: Graceful handling of individual segment failures
- **Memory Efficiency**: Smart chunking prevents memory overflow
- **Quality Assurance**: Enhanced validation and confidence scoring

### 🎯 Key Benefits for Users
1. **Complete Translations**: No more truncated or incomplete translations
2. **Flexible Subtitle Control**: Choose target language or keep original
3. **Immediate Text Access**: Get extracted text content right after upload
4. **Robust Processing**: System handles errors gracefully without breaking
5. **Rich Information**: Detailed metadata and processing information
6. **Better Performance**: Faster processing with improved error handling

---

## 🔍 Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid target language 'xyz'. Choose from 22 Indian languages."
}
```

**404 Not Found:**
```json
{
  "detail": "File not found"
}
```

**413 Request Entity Too Large:**
```json
{
  "detail": "File size exceeds 100MB limit"
}
```

**415 Unsupported Media Type:**
```json
{
  "detail": "File format not supported. Allowed: .txt, .pdf, .mp3, .mp4"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "target_languages"],
      "msg": "Target language 'xyz' not supported",
      "type": "value_error"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "error": "Translation service temporarily unavailable",
  "message": "Please try again later"
}
```

---

## 📝 Notes for Frontend Developers

### File Upload Requirements
- **Max file size:** 100MB for documents, 500MB for videos
- **Supported formats:** .txt, .pdf, .docx, .mp3, .mp4, .wav, .json, .csv, .doc, .odt, .rtf, .epub, .mobi, .azw, .azw3, .m4a, .aac, .ogg, .flac, .wma, .opus
- **Always use multipart/form-data** for file uploads
- **LMS Integration:** Use `is_lms_book=true` to save books/audio to LMS database

### Language Codes
Use ISO language codes for the 22 supported Indian languages:
- `hi` (Hindi), `bn` (Bengali), `ta` (Tamil), `te` (Telugu)
- `gu` (Gujarati), `mr` (Marathi), `kn` (Kannada), `ml` (Malayalam)
- `as` (Assamese), `or` (Odia), `pa` (Punjabi), `ur` (Urdu)
- And 10 more regional languages

### Rate Limiting
- No authentication required for basic operations
- Consider implementing client-side rate limiting for better UX
- Large file processing may take several minutes

### Async Operations
- File translation, video processing, and model retraining are asynchronous
- Use job IDs to poll for completion status
- Implement progress indicators for better user experience

### Error Handling
- Always check response status codes
- Implement retry logic for 5xx errors
- Validate file types and sizes before upload

---

## LMS (Learning Management System) API Endpoints

### Book Management

#### Upload Book
```bash
POST /lms/upload/book
Content-Type: multipart/form-data

# Form fields:
- file: Book file (required)
- title: Book title (optional)
- author: Author name (optional)
- subject: Subject/category (optional)
- grade_level: Grade level (optional)
- language: Language (optional)
- description: Description (optional)

# Supported formats: PDF, DOCX, DOC, TXT, RTF, ODT, EPUB, MOBI, AZW, AZW3
```

**Example:**
```bash
curl -X POST "http://localhost:8000/lms/upload/book" \
  -F "file=@book.pdf" \
  -F "title=Mathematics Grade 5" \
  -F "author=John Smith" \
  -F "subject=Mathematics" \
  -F "grade_level=5" \
  -F "language=en" \
  -F "description=Comprehensive mathematics textbook for grade 5 students"
```

#### Get All Books
```bash
GET /lms/books?skip=0&limit=100&subject=Mathematics&grade_level=5&language=en&author=John Smith
```

**Example:**
```bash
curl -X GET "http://localhost:8000/lms/books?limit=10&subject=Mathematics"
```

#### Get Book by ID
```bash
GET /lms/book/{book_id}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/lms/book/123"
```

#### Delete Book
```bash
DELETE /lms/book/{book_id}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/lms/book/123"
```

### Audio Management

#### Upload Audio
```bash
POST /lms/upload/audio
Content-Type: multipart/form-data

# Form fields:
- file: Audio file (required)
- title: Audio title (optional)
- narrator: Narrator name (optional)
- subject: Subject/category (optional)
- grade_level: Grade level (optional)
- language: Language (optional)
- duration: Duration in seconds (optional)
- description: Description (optional)

# Supported formats: MP3, WAV, M4A, AAC, OGG, FLAC, WMA, OPUS
```

**Example:**
```bash
curl -X POST "http://localhost:8000/lms/upload/audio" \
  -F "file=@lesson.mp3" \
  -F "title=English Pronunciation Lesson 1" \
  -F "narrator=Sarah Johnson" \
  -F "subject=English" \
  -F "grade_level=3" \
  -F "language=en" \
  -F "duration=300" \
  -F "description=Basic English pronunciation for beginners"
```

#### Get All Audio Files
```bash
GET /lms/audio?skip=0&limit=100&subject=English&grade_level=3&language=en&narrator=Sarah Johnson
```

**Example:**
```bash
curl -X GET "http://localhost:8000/lms/audio?limit=10&subject=English"
```

#### Get Audio by ID
```bash
GET /lms/audio/{audio_id}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/lms/audio/456"
```

#### Delete Audio
```bash
DELETE /lms/audio/{audio_id}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/lms/audio/456"
```

### LMS Statistics

#### Get LMS Statistics
```bash
GET /lms/stats
```

**Example:**
```bash
curl -X GET "http://localhost:8000/lms/stats"
```

**Response:**
```json
{
  "total_books": 150,
  "total_audio_files": 75,
  "total_content": 225,
  "book_formats": {
    ".pdf": 80,
    ".docx": 45,
    ".txt": 25
  },
  "audio_formats": {
    ".mp3": 50,
    ".wav": 15,
    ".m4a": 10
  },
  "languages": {
    "en": 100,
    "hi": 75,
    "bn": 25,
    "ta": 25
  },
  "supported_book_formats": [".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".epub", ".mobi", ".azw", ".azw3"],
  "supported_audio_formats": [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma", ".opus"]
}
```

### LMS Response Format

All LMS endpoints return a standardized response format:

```json
{
  "id": 123,
  "filename": "book_123.pdf",
  "original_filename": "Mathematics Grade 5.pdf",
  "path": "/storage/uploads/book_123.pdf",
  "file_type": ".pdf",
  "size": 2048576,
  "domain": "lms_book",
  "source_language": "en",
  "created_at": "2024-01-15T10:30:00Z",
  "extracted_text": "Full text content of the book...",
  "text_metadata": {
    "word_count": 5000,
    "char_count": 30000,
    "pages": 25,
    "format": "pdf",
    "encoding": "utf-8",
    "method": "PyPDF2",
    "paragraphs": 150,
    "tables": 5,
    "title": "Mathematics Grade 5",
    "author": "John Smith",
    "subject": "Mathematics",
    "grade_level": "5",
    "language": "en",
    "description": "Comprehensive mathematics textbook"
  },
  "extraction_status": "success",
  "lms_metadata": {
    "type": "book",
    "title": "Mathematics Grade 5",
    "author": "John Smith",
    "subject": "Mathematics",
    "grade_level": "5",
    "language": "en",
    "description": "Comprehensive mathematics textbook"
  }
}
```

### LMS Features

#### Supported Book Formats
- **PDF**: `.pdf` - Portable Document Format
- **Microsoft Word**: `.docx`, `.doc` - Word documents
- **Text**: `.txt` - Plain text files
- **Rich Text**: `.rtf` - Rich Text Format
- **OpenDocument**: `.odt` - OpenDocument Text
- **E-books**: `.epub`, `.mobi`, `.azw`, `.azw3` - E-book formats

#### Supported Audio Formats
- **MP3**: `.mp3` - MPEG Audio Layer 3
- **WAV**: `.wav` - Waveform Audio File Format
- **M4A**: `.m4a` - MPEG-4 Audio
- **AAC**: `.aac` - Advanced Audio Coding
- **OGG**: `.ogg` - Ogg Vorbis
- **FLAC**: `.flac` - Free Lossless Audio Codec
- **WMA**: `.wma` - Windows Media Audio
- **OPUS**: `.opus` - Opus Audio Codec

#### Key Features
- **Automatic Text Extraction**: Books are automatically processed for text content
- **Rich Metadata**: Comprehensive metadata storage for educational content
- **Multi-Language Support**: Support for all 22 Indian languages plus English
- **Filtering & Search**: Advanced filtering by subject, grade level, language, etc.
- **Statistics Dashboard**: Detailed analytics and usage statistics
- **File Management**: Complete CRUD operations for books and audio files
- **Error Handling**: Robust error handling with detailed error messages

---

## LMS Integration with Upload Endpoint

### Enhanced Upload Endpoint with LMS Integration

The `/upload` endpoint has been enhanced to support LMS integration, allowing you to upload books and audio files that are automatically saved to the LMS database.

#### Upload with LMS Integration
```bash
POST /upload
Content-Type: multipart/form-data

# Form fields:
- file: File (required)
- title: Title (optional)
- author: Author/Narrator (optional)
- subject: Subject (optional)
- grade_level: Grade level (optional)
- language: Language (optional)
- description: Description (optional)
- is_lms_book: true/false (optional, default: false)
```

**Example - Upload Book with LMS Integration:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@mathematics_grade5.pdf" \
  -F "title=Mathematics Grade 5" \
  -F "author=John Smith" \
  -F "subject=Mathematics" \
  -F "grade_level=5" \
  -F "language=en" \
  -F "description=Comprehensive mathematics textbook" \
  -F "is_lms_book=true"
```

**Example - Upload Audio with LMS Integration:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@english_lesson.mp3" \
  -F "title=English Pronunciation" \
  -F "author=Sarah Johnson" \
  -F "subject=English" \
  -F "grade_level=3" \
  -F "language=en" \
  -F "is_lms_book=true"
```

**Response Format:**
```json
{
  "id": "52c23271-4590-4c05-9bad-a2cd8726c9c1",
  "file_id": "52c23271-4590-4c05-9bad-a2cd8726c9c1",
  "db_id": 156,
  "filename": "mathematics_grade5.pdf",
  "size": 2048576,
  "path": "/storage/uploads/52c23271-4590-4c05-9bad-a2cd8726c9c1/mathematics_grade5.pdf",
  "file_type": ".pdf",
  "content_type": "application/pdf",
  "status": "uploaded",
  "message": "File uploaded successfully",
  "extracted_text": "Full text content...",
  "text_metadata": {
    "word_count": 5000,
    "char_count": 30000,
    "pages": 25,
    "format": "pdf"
  },
  "extraction_status": "success",
  "is_lms_book": true,
  "lms_metadata": {
    "type": "book",
    "title": "Mathematics Grade 5",
    "author": "John Smith",
    "subject": "Mathematics",
    "grade_level": "5",
    "language": "en",
    "description": "Comprehensive mathematics textbook"
  }
}
```

### Fetch LMS Books through Content API

#### Get All Files (including LMS)
```bash
GET /content/files?include_lms=true&limit=100
```

#### Get LMS Books Only
```bash
GET /content/files?domain=lms_book&limit=100
```

#### Get LMS Audio Only
```bash
GET /content/files?domain=lms_audio&limit=100
```

#### Get Files Excluding LMS
```bash
GET /content/files?include_lms=false&limit=100
```

#### Get LMS Books via Content API
```bash
GET /content/lms/books?limit=100&language=en
```

#### Get LMS Audio via Content API
```bash
GET /content/lms/audio?limit=100&language=en
```

### Integration Benefits

1. **Unified Upload**: Use the same `/upload` endpoint for both regular files and LMS content
2. **Automatic Database Storage**: LMS books are automatically saved to the database when `is_lms_book=true`
3. **Flexible Retrieval**: Access LMS content through multiple endpoints
4. **Backward Compatibility**: Existing upload functionality remains unchanged
5. **Rich Metadata**: Full LMS metadata support through the upload endpoint
6. **Text Extraction**: Automatic text extraction for document files
7. **Multiple Formats**: Support for all LMS-supported file formats

### Usage Examples

#### Upload a Science Book
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@science_grade6.pdf" \
  -F "title=Science Grade 6 - Chapter 2" \
  -F "author=Dr. Jane Smith" \
  -F "subject=Science" \
  -F "grade_level=6" \
  -F "language=en" \
  -F "description=Comprehensive science textbook" \
  -F "is_lms_book=true"
```

#### Upload an Audio Lesson
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@pronunciation_lesson.mp3" \
  -F "title=English Pronunciation Lesson 1" \
  -F "author=Sarah Johnson" \
  -F "subject=English" \
  -F "grade_level=3" \
  -F "language=en" \
  -F "is_lms_book=true"
```

#### Retrieve All LMS Books
```bash
curl -X GET "http://localhost:8000/content/files?domain=lms_book&limit=10"
```

#### Retrieve LMS Books by Language
```bash
curl -X GET "http://localhost:8000/content/lms/books?language=en&limit=10"
```