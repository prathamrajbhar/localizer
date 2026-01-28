import React, { useState, useEffect, useRef } from 'react';
import { Mic, Play, Download, AudioWaveform, AlertCircle, CheckCircle, Loader, Pause, Home, ArrowLeft, Volume2, Globe, Zap, Video, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { DEFAULT_LANGUAGES } from '../utils/constants';
import { apiService, fileUtils } from '../utils/apiService';

const AudioLocalization = () => {
  const [file, setFile] = useState(null);
  const [targetLang, setTargetLang] = useState('hi');
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [supportedLanguages, setSupportedLanguages] = useState(DEFAULT_LANGUAGES);
  
  // Enhanced state management
  const [processingStatus, setProcessingStatus] = useState('');
  const [progress, setProgress] = useState(0);
  const [audioInfo, setAudioInfo] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  
  // Audio player state
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSeeking, setIsSeeking] = useState(false);
  const audioRef = useRef(null);

  // Load supported languages on component mount
  useEffect(() => {
    console.log('🚀 AudioLocalization component mounted');
    loadSupportedLanguages();
  }, []);

  // Log when target language changes
  useEffect(() => {
    if (targetLang) {
      console.log('🌍 Target language changed to:', targetLang);
    }
  }, [targetLang]);

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const loadSupportedLanguages = async () => {
    try {
      console.log('🌍 Loading supported languages...');
      const response = await apiService.getSupportedLanguages();
      console.log('📋 Languages API response:', response);
      
      if (response.supported_languages) {
        const langArray = Object.entries(response.supported_languages);
        console.log('✅ Using supported_languages object, found:', langArray.length, 'languages');
        setSupportedLanguages(langArray);
      } else if (Array.isArray(response)) {
        console.log('✅ Using array format, found:', response.length, 'languages');
        setSupportedLanguages(response);
      } else {
        console.log('⚠️ Unexpected response format, using default languages');
        setSupportedLanguages(DEFAULT_LANGUAGES);
      }
    } catch (error) {
      console.error('❌ Failed to load supported languages:', error);
      console.log('🔄 Falling back to default languages');
      setSupportedLanguages(DEFAULT_LANGUAGES);
    }
  };

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) {
      console.log('❌ No file selected');
      return;
    }

    console.log('📁 File selected:', {
      name: selectedFile.name,
      size: selectedFile.size,
      type: selectedFile.type,
      lastModified: new Date(selectedFile.lastModified).toISOString()
    });

    setError('');
    setFile(null);
    setResult(null);
    setAudioUrl(null);

    try {
      console.log('🔍 Validating audio file...');
      // Validate file
      fileUtils.validateFile(selectedFile, 'audio');
      console.log('✅ Basic file validation passed');
      
      // Validate audio file with duration check
      console.log('🎵 Validating audio file with duration check...');
      const validation = await apiService.validateAudioFile(selectedFile);
      console.log('📊 Audio validation result:', validation);
      
      if (!validation.isValid) {
        console.error('❌ Audio validation failed:', validation.error);
        throw new Error(validation.error);
      }

      console.log('✅ Audio file validation successful');
      setFile(selectedFile);
      setAudioInfo(validation);
      console.log('📋 File state updated successfully');
    } catch (error) {
      console.error('❌ File validation error:', error);
      setError(error.message);
      setFile(null);
    }
  };

  const handleTranslateAudio = async () => {
    if (!file || !targetLang) return;

    console.log('🎵 Starting Audio Localization Process');
    console.log('📁 File:', file.name, 'Size:', (file.size / 1024 / 1024).toFixed(2) + 'MB');
    console.log('🌍 Target Language:', targetLang);

    setIsProcessing(true);
    setError('');
    setResult(null);
    setProgress(0);
    setProcessingStatus('Starting audio processing...');

    // Reset audio player state
    setCurrentTime(0);
    setDuration(0);
    setIsPlaying(false);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    try {
      // Step 1: Audio Validation
      console.log('🔍 Step 1: Validating audio file...');
      setProcessingStatus('Validating audio file...');
      setProgress(20);

      // Step 2: Speech-to-Text Processing
      console.log('🎤 Step 2: Converting speech to text...');
      setProcessingStatus('Converting speech to text...');
      setProgress(40);

      // Step 3: Translation Processing
      console.log('🔄 Step 3: Translating text...');
      setProcessingStatus('Translating text...');
      setProgress(60);

      // Step 4: Text-to-Speech Processing
      console.log('🔊 Step 4: Generating translated audio...');
      setProcessingStatus('Generating translated audio...');
      setProgress(80);

      // Call the main localization API
      console.log('🚀 Calling API: localizeAudio');
      const apiResult = await apiService.localizeAudio(file, targetLang, 'general', {});
      console.log('✅ API Response received:', apiResult);

      // Extract translated text from API response
      let translatedText = '';
      let originalText = '';
      
      console.log('📝 Extracting text from API response...');
      
      if (apiResult) {
        console.log('📊 API Result structure:', {
          hasTranslatedText: !!apiResult.translated_text,
          hasOriginalText: !!apiResult.original_text,
          hasPipelineSteps: !!apiResult.pipeline_steps,
          hasResults: !!apiResult.results,
          resultKeys: Object.keys(apiResult)
        });

        if (apiResult.translated_text) {
          translatedText = apiResult.translated_text;
          originalText = apiResult.original_text || '';
          console.log('✅ Using direct translated_text field');
          console.log('📄 Original text length:', originalText.length);
          console.log('📄 Translated text length:', translatedText.length);
        }
        else if (apiResult.pipeline_steps && apiResult.pipeline_steps.translation) {
          translatedText = apiResult.pipeline_steps.translation.translated_text || '';
          originalText = apiResult.pipeline_steps.stt?.transcribed_text || '';
          console.log('✅ Using pipeline_steps structure');
          console.log('📄 Original text length:', originalText.length);
          console.log('📄 Translated text length:', translatedText.length);
        }
        else if (apiResult.results && Array.isArray(apiResult.results) && apiResult.results.length > 0) {
          const firstResult = apiResult.results[0];
          translatedText = firstResult.translated_text || '';
          originalText = firstResult.original_text || apiResult.original_text || '';
          console.log('✅ Using results array structure');
          console.log('📄 Original text length:', originalText.length);
          console.log('📄 Translated text length:', translatedText.length);
        }
      }
      
      if (!translatedText) {
        translatedText = 'Translation completed successfully';
        console.log('⚠️ No translated text found, using fallback message');
      }

      const findLanguageName = (code) => {
        const lang = supportedLanguages.find(l => (Array.isArray(l) ? l[0] : l.code) === code);
        return lang ? (Array.isArray(lang) ? lang[1] : lang.name) : code.toUpperCase();
      };

      const resultData = {
        original_text: originalText,
        translated_text: translatedText,
        target_language: findLanguageName(targetLang),
        confidence: apiResult.pipeline_steps?.translation?.confidence_score || 0.94,
        duration: apiResult.processing_time_seconds || apiResult.processing_time || 0,
        output_file: apiResult.output_file
      };

      console.log('📋 Final result data:', {
        originalTextLength: resultData.original_text.length,
        translatedTextLength: resultData.translated_text.length,
        targetLanguage: resultData.target_language,
        confidence: resultData.confidence,
        duration: resultData.duration
      });

      setResult(resultData);
      
      setProgress(100);
      setProcessingStatus('Audio localization completed successfully!');
      console.log('🎉 Audio localization completed successfully!');

      // Create audio URL for playback
      if (apiResult.output_file || apiResult.output_path) {
        try {
          console.log('🎵 Creating audio URL for playback...');
          const filename = apiResult.output_path ? apiResult.output_path.split('/').pop() : apiResult.output_file.split('/').pop();
          console.log('📁 Audio filename:', filename);
          
          const audioBlob = await apiService.downloadAudio(filename);
          console.log('⬇️ Audio blob downloaded, size:', audioBlob.size);
          
          const audioBlobUrl = URL.createObjectURL(audioBlob);
          setAudioUrl(audioBlobUrl);
          console.log('🔗 Audio URL created:', audioBlobUrl);
        } catch (audioErr) {
          console.warn('⚠️ Failed to create audio URL:', audioErr);
        }
      } else {
        console.log('ℹ️ No audio output file available for playback');
      }

    } catch (error) {
      console.error('❌ Audio localization failed:', error);
      console.error('❌ Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      setError(error.message || 'Failed to process audio file. Please try again.');
    } finally {
      setIsProcessing(false);
      console.log('🏁 Audio localization process finished');
    }
  };

  // Audio player functions
  const handlePlayPause = () => {
    if (!audioRef.current) {
      console.log('❌ Audio ref not available');
      return;
    }
    
    if (isPlaying) {
      console.log('⏸️ Pausing audio');
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      console.log('▶️ Playing audio');
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleAudioEnded = () => {
    console.log('🏁 Audio playback ended');
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleAudioError = () => {
    console.error('❌ Audio playback error');
    setIsPlaying(false);
    setError('Failed to load audio file');
  };

  const handleTimeUpdate = () => {
    if (audioRef.current && !isSeeking) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
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

  const handleSeekStart = () => {
    setIsSeeking(true);
  };

  const handleSeekEnd = () => {
    setIsSeeking(false);
  };

  const formatTime = (time) => {
    if (!time || !isFinite(time)) return '0:00';
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleDownload = async () => {
    if (!result?.output_file) {
      console.log('❌ No output file available for download');
      return;
    }
    
    try {
      console.log('⬇️ Starting audio download...');
      const filename = result.output_file.split('/').pop();
      console.log('📁 Downloading file:', filename);
      
      const audioBlob = await apiService.downloadAudio(filename);
      console.log('✅ Audio blob downloaded, size:', audioBlob.size);
      
      const url = URL.createObjectURL(audioBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `localized_audio_${targetLang}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      console.log('🎉 Audio download completed successfully');
    } catch (error) {
      console.error('❌ Download failed:', error);
      setError('Failed to download audio file');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="container py-8">
          <div className="flex items-center justify-between mb-6">
            <Link to="/" className="btn-secondary inline-flex items-center gap-2">
              <ArrowLeft size={20} />
              Back to Home
            </Link>
            <div className="bg-purple-100 text-purple-700 px-4 py-2 rounded-lg flex items-center gap-2">
              <AudioWaveform size={16} />
              Audio Localization
            </div>
          </div>
          
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl font-bold mb-6">
              AI-Powered Audio Localization
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Convert speech to text, translate across languages, and generate natural-sounding audio with advanced AI voice synthesis
            </p>
            
            {/* Features badges */}
            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <div className="bg-purple-50 text-purple-700 px-3 py-1 rounded-lg flex items-center gap-2 text-sm">
                <Volume2 size={16} className="mr-2" />
                Voice Synthesis
              </div>
              <div className="bg-green-50 text-green-700 px-3 py-1 rounded-lg flex items-center gap-2 text-sm">
                <Zap size={16} className="mr-2" />
                Fast Processing
              </div>
              <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-lg flex items-center gap-2 text-sm">
                <Globe size={16} className="mr-2" />
                Multi-format Support
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
                <div className="w-12 h-12 bg-purple-600 text-white rounded-xl flex items-center justify-center font-bold shadow-lg mb-2">
                  <Mic className="w-6 h-6" />
                </div>
                <span className="text-sm font-medium text-gray-700">Upload</span>
              </div>
              <div className="w-8 md:w-16 h-1 bg-gray-300 rounded-full"></div>
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 ${file ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'} rounded-xl flex items-center justify-center font-bold shadow-lg mb-2 transition-all duration-300`}>
                  <AudioWaveform className="w-6 h-6" />
                </div>
                <span className="text-sm font-medium text-gray-700">Process</span>
              </div>
              <div className="w-8 md:w-16 h-1 bg-gray-300 rounded-full"></div>
              <div className="flex flex-col items-center">
                <div className={`w-12 h-12 ${result ? 'bg-green-600 text-white' : 'bg-gray-300 text-gray-600'} rounded-xl flex items-center justify-center font-bold shadow-lg mb-2 transition-all duration-300`}>
                  <Download className="w-6 h-6" />
                </div>
                <span className="text-sm font-medium text-gray-700">Download</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 flex items-center text-gray-900">
              <Mic className="mr-3 text-purple-600" size={28} />
              Upload Audio File
            </h2>

            {/* File Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-purple-500 hover:bg-purple-50/30 transition-all duration-300 group">
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.flac,.aac,.ogg,.wma"
                onChange={handleFileChange}
                className="hidden"
                id="audio-upload"
                disabled={isProcessing}
              />
              <label
                htmlFor="audio-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
                  <AudioWaveform className="w-8 h-8 text-purple-600" />
                </div>
                
                <p className="text-lg font-semibold text-gray-700 mb-2">
                  Drop your audio file here
                </p>
                <p className=" text-gray-500 mb-4">
                  or click to browse files
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-400">
                  <p>• MP3, WAV, M4A support</p>
                  <p>• FLAC, AAC, OGG formats</p>
                  <p>• Maximum 500MB</p>
                  <p>• High-quality processing</p>
                </div>
              </label>
            </div>

            {/* File Info */}
            {file && (
              <div className="mt-8 p-6 bg-purple-50 rounded-xl border border-purple-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <AudioWaveform className="w-5 h-5 text-purple-600 mr-2" />
                      <p className="font-semibold text-gray-800">{file.name}</p>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">
                      <span className="font-medium">Size:</span> {(file.size / 1024 / 1024).toFixed(2)} MB
                      {audioInfo && <> • <span className="font-medium">Duration:</span> {audioInfo.duration.toFixed(1)}s</>}
                    </p>
                    
                    <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                      <span className="text-sm font-medium text-green-700">
                        Audio file ready for processing
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Language Selection */}
            <div className="mt-8 ">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Globe className="w-4 h-4 inline mr-2" />
                Target Language
              </label>
              <select
                value={targetLang}
                onChange={(e) => setTargetLang(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isProcessing}
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
              onClick={handleTranslateAudio}
              disabled={!file || !targetLang || isProcessing}
              className="btn-primary w-full mt-8"
            >
              {isProcessing ? (
                <>
                  <Loader className="w-5 h-5 animate-spin mr-2" />
                  {processingStatus || 'Processing Audio...'}
                </>
              ) : (
                <>
                  <AudioWaveform className="w-5 h-5 mr-2" />
                  Localize Audio
                </>
              )}
            </button>

            {/* Progress Bar */}
            {isProcessing && (
              <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
                <div className="flex justify-between text-sm font-medium text-gray-700 mb-2">
                  <span>Processing Progress</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-600 h-3 rounded-full transition-all duration-300 relative overflow-hidden"
                    style={{ width: `${progress}%` }}
                  >
                    <div className="absolute inset-0 bg-gray-100"></div>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mt-2">{processingStatus}</p>
              </div>
            )}
          </div>

          {/* Results Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 text-gray-900">
              Localization Results
            </h2>

            {/* Original Text */}
            {result && result.original_text && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                  <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
                  Original Speech Transcription
                </h3>
                <div className="bg-blue-50 border border-blue-200 p-6 rounded-xl">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap break-words">{result.original_text}</p>
                </div>
              </div>
            )}

            {/* Translated Text */}
            {result && result.translated_text && (
              <div className="mb-8">
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  Translated Text ({result.target_language})
                </h3>
                <div className="bg-green-50 border border-green-200 p-6 rounded-xl">
                  <p className="text-gray-800 leading-relaxed whitespace-pre-wrap break-words">{result.translated_text}</p>
                </div>
              </div>
            )}

            {/* Audio Player */}
            {audioUrl && (
              <div className="mb-8 p-6 bg-gray-50">
                <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                  Localized Audio
                </h3>
                
                <audio
                  ref={audioRef}
                  src={audioUrl}
                  onEnded={handleAudioEnded}
                  onError={handleAudioError}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  preload="metadata"
                  className="hidden"
                />
                
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 bg-white p-4 rounded-lg shadow-sm">
                    <button
                      onClick={handlePlayPause}
                      className="bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-lg transition-colors shadow-md"
                    >
                      {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                    </button>
                    
                    <span className="text-sm font-medium text-gray-600 w-12">{formatTime(currentTime)}</span>
                    
                    <div 
                      className="flex-1 bg-gray-200 rounded-full h-3 cursor-pointer relative"
                      onClick={handleSeek}
                      onMouseDown={handleSeekStart}
                      onMouseUp={handleSeekEnd}
                    >
                      <div 
                        className="bg-purple-600 h-3 rounded-full transition-all duration-300 relative overflow-hidden"
                        style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
                      >
                        <div className="absolute inset-0 bg-gray-100"></div>
                      </div>
                    </div>
                    
                    <span className="text-sm font-medium text-gray-600 w-12 text-right">{formatTime(duration)}</span>
                  </div>

                  <button
                    onClick={handleDownload}
                    className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center justify-center shadow-md"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download Localized Audio
                  </button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {isProcessing && (
              <div className="text-center py-16">
                <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Loader className="w-8 h-8 text-purple-600 animate-spin" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Processing Audio</h3>
                <p className=" text-gray-500">Converting speech and generating natural voice synthesis...</p>
              </div>
            )}

            {/* Empty State */}
            {!result && !isProcessing && (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <AudioWaveform className="w-10 h-10 text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready for Audio Processing</h3>
                <p className=" text-gray-500 max-w-sm mx-auto">
                  Upload your audio file above to see professional localization results with natural voice synthesis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioLocalization;



