import React, { useState, useEffect, useRef } from 'react';
import { FileText, Upload, Languages, Download, AlertCircle, CheckCircle, Loader, ArrowLeft, Globe, Zap, Volume2, Play, Pause, Video, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiService } from '../utils/apiService';
import { DEFAULT_LANGUAGES } from '../utils/constants';
import { validateFile } from '../utils/fileUtils';

const DocumentTranslation = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [targetLanguage, setTargetLanguage] = useState('hi');
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [originalText, setOriginalText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [isDetecting, setIsDetecting] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [supportedLanguages, setSupportedLanguages] = useState(DEFAULT_LANGUAGES);
  const [fileId, setFileId] = useState(null); // Store the uploaded file ID
  const [textMetadata, setTextMetadata] = useState(null); // Store text metadata
  
  // Text-to-Speech states
  const [isTTSLoading, setIsTTSLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [ttsError, setTtsError] = useState('');
  const audioRef = useRef(null);

  // Load supported languages from API and track page view
  useEffect(() => {
    const loadSupportedLanguages = async () => {
      try {
        const response = await apiService.getSupportedLanguages();
        if (response.supported_languages) {
          const langArray = Object.entries(response.supported_languages);
          setSupportedLanguages(langArray);
        } else if (Array.isArray(response)) {
          // Handle case where API returns array format
          setSupportedLanguages(response);
        }
      } catch (err) {
        console.error('Failed to load supported languages:', err);
        // Fallback to default languages
        setSupportedLanguages(DEFAULT_LANGUAGES);
      }
    };

    loadSupportedLanguages();
  }, []);

  // Handle file upload and language detection
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError('');
    
    // Validate file
    const validation = validateFile(file, ['txt', 'pdf', 'docx', 'doc', 'rtf'], 100);
    if (!validation.isValid) {
      setError(validation.error);
      return;
    }

    setSelectedFile(file);
    setDetectedLanguage('');
    setOriginalText('');
    setTranslatedText('');
    setConfidence(0);
    setFileId(null);
    setTextMetadata(null);

    // Upload file and detect language
    await handleUploadAndDetect(file);
  };

  // Upload file and detect language
  const handleUploadAndDetect = async (file) => {
    setIsDetecting(true);
    setError('');

    try {
      console.log(`Uploading ${file.name} for text extraction...`);
      
      // Use the new /content/upload endpoint with text extraction
      const uploadResponse = await apiService.uploadFile(file, 'general', 'auto');
      
      console.log('Upload response:', uploadResponse);
      
      // Store file ID for translation
      if (uploadResponse.id) {
        setFileId(uploadResponse.id);
        console.log('File ID set:', uploadResponse.id);
      } else {
        console.warn('No file ID in upload response');
      }
      
      // Extract text from the new API response format
      let textContent = '';
      if (uploadResponse.extracted_text) {
        textContent = uploadResponse.extracted_text;
        console.log('Text extracted, length:', textContent.length);
      } else if (uploadResponse.content) {
        textContent = uploadResponse.content;
        console.log('Text from content field, length:', textContent.length);
      } else {
        // Fallback for text files - try reading directly
        if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
          try {
            textContent = await file.text();
            console.log('Text file read directly, length:', textContent.length);
          } catch (textError) {
            console.warn('Failed to read text file directly:', textError);
          }
        }
      }
      
      // Store text metadata if available
      if (uploadResponse.text_metadata) {
        setTextMetadata(uploadResponse.text_metadata);
        console.log('Text metadata:', uploadResponse.text_metadata);
      }
      
      // Check extraction status
      if (uploadResponse.extraction_status === 'failed') {
        throw new Error('Text extraction failed. The file might be corrupted or in an unsupported format.');
      }
      
      if (!textContent || textContent.trim() === '') {
        throw new Error('Could not extract text content from file. Please ensure the file contains readable text.');
      }
      
      console.log('Detecting language for text of length:', textContent.length);
      
      // Detect language
      const detectionResponse = await apiService.detectLanguage({ text: textContent });
      
      console.log('Language detected:', detectionResponse.detected_language, 'Confidence:', detectionResponse.confidence);
      
      // Ensure we have a valid language code for translation
      let detectedLang = detectionResponse.detected_language;
      if (!detectedLang || detectedLang === 'auto') {
        detectedLang = 'en'; // Default to English if detection fails or returns 'auto'
      }
      
      setDetectedLanguage(detectedLang);
      setOriginalText(textContent);
      setConfidence(detectionResponse.confidence * 100);
      
      console.log('Upload and detection completed:', {
        fileId: uploadResponse.id,
        textLength: textContent.length,
        detectedLanguage: detectedLang,
        originalDetectedLanguage: detectionResponse.detected_language,
        confidence: detectionResponse.confidence
      });
    } catch (err) {
      console.error('Upload/Detection error:', err);
      setError('Failed to upload or detect language: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsDetecting(false);
    }
  };

  // Handle translation
  const handleTranslate = async () => {
    if ((!originalText && !fileId) || !targetLanguage) {
      setError('Please upload a file and select target language');
      return;
    }

    setIsTranslating(true);
    setError('');
    setTranslatedText('');

    try {
      console.log('Starting translation...', { 
        fileId, 
        targetLanguage, 
        detectedLanguage, 
        originalText: originalText ? `present (${originalText.length} chars)` : 'missing',
        hasFileId: !!fileId,
        hasOriginalText: !!originalText
      });
      
      // Use file_id if available, otherwise use text
      let translationParams;
      if (fileId) {
        translationParams = {
          file_id: fileId,
          source_language: detectedLanguage || 'en', // Use detected language or default to 'en'
          target_languages: [targetLanguage],
          domain: 'general',
          apply_localization: true
        };
        console.log('Using file_id for translation:', fileId, 'with source language:', detectedLanguage || 'en');
        console.log('Translation params:', translationParams);
      } else if (originalText) {
        translationParams = {
          text: originalText,
          source_language: detectedLanguage || 'en', // Use detected language or default to 'en'
          target_languages: [targetLanguage],
          domain: 'general',
          apply_localization: true
        };
        console.log('Using text for translation, length:', originalText.length, 'with source language:', detectedLanguage || 'en');
        console.log('Translation params:', translationParams);
      } else {
        console.error('No file ID or text content available for translation');
        throw new Error('No file ID or text content available for translation');
      }

      const result = await apiService.translateText(translationParams);
      
      console.log('Translation result:', result);

      // Get the translated text from the first result
      if (result.results && result.results.length > 0) {
        setTranslatedText(result.results[0].translated_text);
      } else if (result.translated_text) {
        setTranslatedText(result.translated_text);
      } else {
        setTranslatedText('Translation completed successfully');
      }
    } catch (err) {
      console.error('Translation error:', err);
      setError('Failed to translate: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsTranslating(false);
    }
  };

  // Handle download
  const handleDownload = () => {
    if (!translatedText) {
      setError('No translated text to download');
      return;
    }

    try {
      const blob = new Blob([translatedText], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `translated_${selectedFile.name.split('.')[0]}_${targetLanguage}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download file: ' + err.message);
    }
  };

  // Text-to-Speech functions
  const generateTTS = async () => {
    if (!translatedText) return;

    setIsTTSLoading(true);
    setTtsError('');
    
    try {
      console.log('🎵 Generating TTS for translated text...');
      console.log('📝 Text length:', translatedText.length);
      console.log('🌍 Target language:', targetLanguage);
      console.log('📝 Text preview:', translatedText.substring(0, 100) + '...');

      // Validate text length (limit to reasonable size for TTS)
      const maxLength = 1000;
      const textToProcess = translatedText.length > maxLength 
        ? translatedText.substring(0, maxLength) + '...'
        : translatedText;

      // Validate and sanitize text (remove any problematic characters)
      const sanitizedText = textToProcess.replace(/[^\w\s.,!?;:'"()-]/g, ' ').trim();
      
      if (!sanitizedText) {
        throw new Error('No valid text content to convert to speech');
      }

      console.log('📝 Processing text length:', sanitizedText.length);
      console.log('📝 Sanitized text preview:', sanitizedText.substring(0, 50) + '...');

      // Use a fallback language if target language might not be supported
      const ttsLanguage = targetLanguage || 'en';
      console.log('🌍 Using TTS language:', ttsLanguage);

      const response = await apiService.textToSpeech(
        sanitizedText,
        ttsLanguage,
        1.0, // Default voice speed
        'mp3'
      );

      console.log('✅ TTS generated successfully:', response);

      if (response.output_file) {
        // Download the audio file and create a blob URL
        const audioBlob = await apiService.downloadAudio(response.output_file);
        const audioBlobUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(audioBlobUrl);
        
        // Set up audio element
        if (audioRef.current) {
          audioRef.current.src = audioBlobUrl;
          audioRef.current.load();
        }
      } else {
        console.warn('⚠️ No output_file in TTS response:', response);
        setTtsError('Audio generated but no file path returned');
      }
    } catch (error) {
      console.error('❌ TTS generation failed:', error);
      console.error('❌ Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      
      let errorMessage = 'Failed to generate audio';
      if (error.response?.status === 422) {
        errorMessage = 'Invalid request parameters. Please check the text and language settings.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setTtsError(errorMessage);
    } finally {
      setIsTTSLoading(false);
    }
  };

  const togglePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e) => {
    if (!audioRef.current) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const width = rect.width;
    const newTime = (clickX / width) * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };


  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleDurationChange = () => setDuration(audio.duration);
    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };
    const handleLoadStart = () => console.log('🎵 Audio loading started');
    const handleCanPlay = () => console.log('🎵 Audio ready to play');
    const handleError = (e) => {
      console.error('❌ Audio error:', e);
      setTtsError('Audio playback error');
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
      audio.removeEventListener('error', handleError);
    };
  }, [audioUrl]);

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  return (
    <div className="min-h-screen" style={{backgroundColor: '#fff7ed'}}>
      {/* Custom CSS for audio player */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 2px solid #ffffff;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: 2px solid #ffffff;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .slider::-webkit-slider-track {
          background: #e5e7eb;
          height: 4px;
          border-radius: 2px;
        }
        
        .slider::-moz-range-track {
          background: #e5e7eb;
          height: 4px;
          border-radius: 2px;
        }
      `}</style>
      {/* Header Section */}
      <div className="bg-white" style={{borderBottom: '3px solid #FF9933'}}>
        <div className="container py-8">
          <div className="flex items-center justify-between mb-6">
            <Link to="/" className="btn-secondary inline-flex items-center gap-2">
              <ArrowLeft size={20} />
              Back to Home
            </Link>
            <div className="px-4 py-2 rounded-lg flex items-center gap-2" 
                 style={{backgroundColor: '#fff7ed', color: '#FF9933', border: '2px solid #FF9933'}}>
              <FileText size={18} />
              Document Translation
            </div>
          </div>
          
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl font-bold mb-6" style={{color: '#000080'}}>
              AI-Powered Document Translation
            </h1>
            <p className="text-lg mb-8" style={{color: '#4b5563'}}>
              Upload documents in any format and get professional-grade translations across 22+ Indian languages with enterprise-level accuracy
            </p>
            
            {/* Features badges */}
            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <div className="px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium" 
                   style={{backgroundColor: '#fff7ed', color: '#FF9933', border: '1px solid #FFB366'}}>
                <FileText size={16} />
                Multi-format Support
              </div>
              <div className="px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium" 
                   style={{backgroundColor: '#f0fdf4', color: '#138808', border: '1px solid #22c55e'}}>
                <Zap size={16} />
                99% Accuracy
              </div>
              <div className="px-4 py-2 rounded-lg flex items-center gap-2 text-sm font-medium" 
                   style={{backgroundColor: '#eff6ff', color: '#000080', border: '1px solid #3b82f6'}}>
                <Globe size={16} />
                22+ Languages
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        {/* Demo Video Notice */}
        <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <Video className="h-5 w-5 text-blue-600 mt-0.5" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> We're currently running on CPU processing as we can't afford GPU servers yet. Some features may take longer or occasionally not work. Watch our demo video to see the full potential!
              </p>
              <div className="mt-2">
                <a 
                  href="https://youtu.be/CuezATiplts" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-sm font-medium text-blue-800 hover:text-blue-900"
                >
                  <Video size={16} className="mr-1" />
                  Watch Demo Video
                  <ChevronRight size={16} className="ml-1" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-6 bg-red-50 border border-red-200 rounded-xl">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-red-500 mr-3" />
              <span className="text-red-700 font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Process Flow */}
        <div className="mb-12">
          <div className="flex items-center justify-center max-w-4xl mx-auto">
            <div className="flex items-center space-x-4 md:space-x-8">
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-xl flex items-center justify-center font-bold shadow-lg mb-2">
                  1
                </div>
                <span className="text-sm font-medium text-gray-700">Upload</span>
              </div>
              <div className="w-8 md:w-16 h-1 bg-gray-300 rounded-full"></div>
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 ${detectedLanguage ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'} rounded-xl flex items-center justify-center font-bold shadow-lg mb-2 transition-all duration-300`}>
                  2
                </div>
                <span className="text-sm font-medium text-gray-700">Detect</span>
              </div>
              <div className="w-8 md:w-16 h-1 bg-gray-300 rounded-full"></div>
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 ${translatedText ? 'bg-green-600 text-white' : 'bg-gray-300 text-gray-600'} rounded-xl flex items-center justify-center font-bold shadow-lg mb-2 transition-all duration-300`}>
                  3
                </div>
                <span className="text-sm font-medium text-gray-700">Translate</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 flex items-center text-gray-900">
              <Upload className="mr-3 text-blue-600" size={24} />
              Upload Document
            </h2>

            {/* File Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-500 hover:bg-blue-50/30 transition-all duration-300 group">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".txt,.pdf,.docx,.doc,.rtf"
                className="hidden"
                id="file-upload"
                disabled={isDetecting}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
                  <FileText className="w-8 h-8 text-blue-600" />
                </div>
                <p className="text-lg font-semibold text-gray-700 mb-2">
                  Click to upload or drag and drop
                </p>
                <p className="text-gray-500 mb-4">
                  Supports: TXT, PDF, DOCX, DOC, RTF (Max 100MB)
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-400">
                  <p>• PDF: Advanced text extraction</p>
                  <p>• Word: Complete document processing</p>
                  <p>• Text: Direct processing</p>
                  <p>• Auto language detection</p>
                </div>
              </label>
            </div>

            {/* File Info */}
            {selectedFile && (
              <div className="mt-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <FileText className="w-5 h-5 text-blue-600 mr-2" />
                      <p className="font-semibold text-gray-800">{selectedFile.name}</p>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">
                      <span className="font-medium">Type:</span> {selectedFile.type || 'Unknown'} • 
                      <span className="font-medium"> Size:</span> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      {fileId && <> • <span className="font-medium">ID:</span> {fileId}</>}
                    </p>
                    
                    {textMetadata && (
                      <div className="grid grid-cols-2 gap-4 p-3 bg-white rounded-lg border mb-3">
                        <div className="text-sm">
                          <span className="font-medium text-gray-600">Words:</span> {textMetadata.word_count}
                        </div>
                        <div className="text-sm">
                          <span className="font-medium text-gray-600">Characters:</span> {textMetadata.char_count}
                        </div>
                        {textMetadata.pages && (
                          <div className="text-sm">
                            <span className="font-medium text-gray-600">Pages:</span> {textMetadata.pages}
                          </div>
                        )}
                        {textMetadata.format && (
                          <div className="text-sm">
                            <span className="font-medium text-gray-600">Format:</span> {textMetadata.format.toUpperCase()}
                          </div>
                        )}
                      </div>
                    )}

                    {detectedLanguage && (
                      <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                        <span className="text-sm font-medium text-green-700">
                          Language Detected: {detectedLanguage} ({confidence.toFixed(1)}% confidence)
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {isDetecting && (
                    <div className="flex items-center ml-4">
                      <Loader className="w-6 h-6 text-blue-600 animate-spin mr-2" />
                      <span className="text-sm text-gray-600">
                        {(() => {
                          const ext = selectedFile.name.split('.').pop().toLowerCase();
                          return ext === 'txt' ? 'Reading...' : 
                                 ext === 'pdf' ? 'Extracting...' :
                                 ext === 'docx' || ext === 'doc' ? 'Processing...' :
                                 'Processing...';
                        })()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Language Selection */}
            <div className="mt-8">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Languages className="w-4 h-4 inline mr-2" />
                Target Language
              </label>
              <select
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isTranslating}
              >
                {supportedLanguages.map((lang) => {
                  const code = Array.isArray(lang) ? lang[0] : lang.code;
                  const name = Array.isArray(lang) ? lang[1] : lang.name;
                  return (
                    <option key={code} value={code}>
                      {name}
                    </option>
                  );
                })}
              </select>
            </div>

            {/* Translate Button */}
            <button
              onClick={handleTranslate}
              disabled={(!originalText && !fileId) || !targetLanguage || isTranslating}
              className="btn-primary w-full mt-8"
            >
              {isTranslating ? (
                <>
                  <Loader className="w-5 h-5 animate-spin mr-2" />
                  Translating Document...
                </>
              ) : (
                <>
                  <Languages className="w-5 h-5 mr-2" />
                  Translate Document
                </>
              )}
            </button>
          </div>

          {/* Results Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 text-gray-900">
              Translation Results
            </h2>

            {/* Original Text */}
            {originalText && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                  <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                  Original Text ({detectedLanguage})
                </h3>
                <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl max-h-48 overflow-y-auto">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{originalText}</p>
                </div>
              </div>
            )}

            {/* Translated Text */}
            {translatedText && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  Translated Text ({targetLanguage})
                </h3>
                <div className="bg-green-50 border border-green-200 p-6 rounded-xl max-h-48 overflow-y-auto">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{translatedText}</p>
                </div>

                <button
                  onClick={handleDownload}
                  className="mt-6 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Translation
                </button>

                {/* Professional Audio Player */}
       <div className="mt-8 bg-white border border-gray-200 rounded-lg p-6">
         <div className="flex items-center justify-between mb-4">
           <h3 className="text-lg font-semibold text-gray-800">Text-to-Speech</h3>
           <button
             onClick={generateTTS}
             disabled={isTTSLoading}
             className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-50 flex items-center"
           >
             {isTTSLoading ? (
               <>
                 <Loader className="w-4 h-4 mr-2 animate-spin" />
                 Generating...
               </>
             ) : (
               <>
                 <Volume2 className="w-4 h-4 mr-2" />
                 Generate Audio
               </>
             )}
           </button>
         </div>

         {/* Hidden audio element */}
         <audio ref={audioRef} preload="metadata" />
         
         {audioUrl ? (
           <div className="space-y-4">
             {/* Simple Seek Bar */}
             <div>
               <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                 <span>{formatTime(currentTime)}</span>
                 <span>{formatTime(duration)}</span>
               </div>
               <div 
                 className="relative w-full h-2 bg-gray-200 rounded-full cursor-pointer"
                 onClick={handleSeek}
               >
                 <div 
                   className="absolute top-0 left-0 h-full bg-blue-600 rounded-full transition-all duration-100"
                   style={{ width: duration ? `${(currentTime / duration) * 100}%` : '0%' }}
                 />
               </div>
             </div>

             {/* Simple Play Button */}
             <div className="flex justify-center">
               <button
                 onClick={togglePlayPause}
                 className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center transition-all"
               >
                 {isPlaying ? (
                   <Pause className="w-6 h-6" />
                 ) : (
                   <Play className="w-6 h-6 ml-1" />
                 )}
               </button>
             </div>
           </div>
         ) : (
           <div className="text-center py-8">
             <Volume2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
             <p className="text-gray-500">Click "Generate Audio" to create audio from translated text</p>
           </div>
         )}

         {/* Error Display */}
         {ttsError && (
           <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
             <div className="flex items-center">
               <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
               <span className="text-red-700 font-medium">{ttsError}</span>
             </div>
           </div>
         )}
       </div>
              </div>
            )}

            {/* Loading State */}
            {isTranslating && (
              <div className="text-center py-16">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Loader className="w-8 h-8 text-blue-600 animate-spin" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Processing Translation</h3>
                <p className="text-gray-500">Using advanced AI models to ensure accuracy...</p>
              </div>
            )}

            {/* Empty State */}
            {!originalText && !isTranslating && (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <FileText className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready for Translation</h3>
                <p className="text-gray-500 max-w-sm mx-auto">
                  Upload your document above to see professional translation results here
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentTranslation;
