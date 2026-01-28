import React, { useState, useEffect } from 'react';
import { Video, Upload, Download, Languages, Play, CheckCircle, AlertCircle, ArrowLeft, Globe, Zap, Loader, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { DEFAULT_LANGUAGES } from '../utils/constants';
import { apiService, fileUtils } from '../utils/apiService';

const VideoLocalization = () => {
  const [file, setFile] = useState(null);
  const [targetLang, setTargetLang] = useState('');
  const [result, setResult] = useState(null);
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState('');
  const [error, setError] = useState('');
  const [supportedLanguages, setSupportedLanguages] = useState(DEFAULT_LANGUAGES);
  const [videoUrl, setVideoUrl] = useState(null);
  const [isVideoLoading, setIsVideoLoading] = useState(false);
  const [subtitles, setSubtitles] = useState([]);
  const [currentSubtitle, setCurrentSubtitle] = useState(null);

  // Load supported languages from API
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

  // Cleanup video URL on unmount
  useEffect(() => {
    return () => {
      if (videoUrl) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  }, [videoUrl]);



  // Handle file upload
  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    try {
      fileUtils.validateFile(selectedFile, 'video');
      setFile(selectedFile);
      setResult(null);
      setError('');
      setStep(2);
    } catch (err) {
      setError(err.message || 'Invalid video file');
      setFile(null);
      setStep(1);
    }
  };


  // Handle video processing
  const handleLocalizeVideo = async () => {
    if (!file || !targetLang) return;

    try {
      setIsProcessing(true);
      setStep(3);
      setError('');
      setProcessingStage('Processing video...');

      // Call the video localization API with target language for subtitle translation
      const response = await apiService.localizeVideo(
        file,
        targetLang,
        'general',
        true, // include subtitles
        false, // include dubbed audio
        targetLang // target language for subtitle translation
      );
      
      // Find language name from supported languages
      const findLanguageName = (code) => {
        const lang = supportedLanguages.find((lang) => {
          const langCode = Array.isArray(lang) ? lang[0] : lang.code;
          return langCode === code;
        });
        return lang ? (Array.isArray(lang) ? lang[1] : lang.name) : code;
      };

      // Parse the response outputs array
      let subtitlesFile = null;
      let videoWithSubtitles = null;
      let transcriptFile = null;
      
      if (response.outputs && Array.isArray(response.outputs)) {
        response.outputs.forEach(output => {
          if (output.type === 'subtitles') {
            subtitlesFile = output;
          } else if (output.type === 'video_with_subtitles') {
            videoWithSubtitles = output;
          } else if (output.type === 'transcript') {
            transcriptFile = output;
          }
        });
      }

      setResult({
        video_file: file.name,
        target_language: findLanguageName(targetLang),
        subtitles_file: subtitlesFile,
        video_with_subtitles: videoWithSubtitles,
        transcript_file: transcriptFile,
        duration: response.processing_details?.original_duration || 10.0,
        confidence: response.translation_confidence || 0.92,
        output_files: response.outputs,
        processing_time: response.processing_time,
        status: response.status,
        // New fields from updated API
        detected_language: response.detected_language,
        subtitle_translated: response.translated || false,
        subtitle_content: response.subtitle_content,
        segment_count: response.processing_details?.segments_translated || 0
      });

      setStep(4);
    } catch (err) {
      setError('Failed to process video: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsProcessing(false);
      setProcessingStage('');
    }
  };

  // Handle video download
  const handleDownloadVideo = async (filename) => {
    if (!filename) return;
    
    try {
      const blob = await apiService.downloadVideo(filename);
      fileUtils.downloadBlob(blob, filename);
    } catch (err) {
      setError('Failed to download video: ' + err.message);
    }
  };

  // Load video for playback
  const loadVideoForPlayback = async (filename) => {
    if (!filename) return;
    
    setIsVideoLoading(true);
    try {
      const blob = await apiService.downloadVideo(filename);
      const url = URL.createObjectURL(blob);
      setVideoUrl(url);
    } catch (err) {
      setError('Failed to load video: ' + err.message);
    } finally {
      setIsVideoLoading(false);
    }
  };

  // Enhanced subtitle loading with direct content support
  const loadSubtitles = async (filename, subtitleContent = null) => {
    try {
      let srtText;
      
      if (subtitleContent) {
        // Use direct subtitle content if available (more efficient)
        console.log('Using direct subtitle content from API response');
        srtText = subtitleContent;
      } else {
        // Fallback to downloading the file
        console.log('Downloading subtitle file:', filename);
        const blob = await apiService.downloadVideo(filename);
        srtText = await blob.text();
      }
      
      const parsed = parseSRT(srtText);
      setSubtitles(parsed);
      console.log('Subtitles loaded successfully:', parsed.length);
    } catch (err) {
      console.error('Failed to load subtitles:', err);
    }
  };

  // Fixed SRT parser for Windows CRLF format
  const parseSRT = (srtText) => {
    const subtitles = [];
    
    // Handle Windows CRLF line endings
    const normalizedText = srtText.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    
    // Split by double newlines to get subtitle blocks
    const blocks = normalizedText.trim().split('\n\n');
    
    console.log('Parsing SRT:', blocks.length, 'blocks found');
    
    blocks.forEach((block, index) => {
      const lines = block.trim().split('\n');
      console.log(`Block ${index + 1}:`, lines.length, 'lines');
      
      // Each subtitle block should have: index, time, text, (optional empty line)
      if (lines.length >= 3) {
        const subtitleIndex = lines[0].trim();
        const timeRange = lines[1].trim();
        const textLines = lines.slice(2).filter(line => line.trim() !== ''); // Remove empty lines
        const text = textLines.join('\n').trim();
        
        // Parse time range
        if (timeRange.includes(' --> ')) {
          const [start, end] = timeRange.split(' --> ');
          
          // Remove [TRANSLATED] prefix if present
          const cleanText = text.replace(/^\[TRANSLATED\]\s*/, '');
          
          subtitles.push({
            index: parseInt(subtitleIndex),
            start: start.trim(),
            end: end.trim(),
            text: cleanText,
            startTime: timeToSeconds(start.trim()),
            endTime: timeToSeconds(end.trim())
          });
          
          console.log(`Added subtitle ${subtitleIndex}:`, cleanText.substring(0, 50) + '...');
        } else {
          console.warn('Invalid time range format:', timeRange);
        }
      } else {
        console.warn(`Block ${index + 1} has only ${lines.length} lines, skipping`);
      }
    });
    
    console.log('Total subtitles parsed:', subtitles.length);
    return subtitles;
  };

  // Convert time to seconds (handles HH:MM:SS,mmm format)
  const timeToSeconds = (timeStr) => {
    try {
      // Handle format: HH:MM:SS,mmm
      const [time, ms] = timeStr.split(',');
      const [h, m, s] = time.split(':').map(Number);
      const milliseconds = ms ? parseInt(ms) / 1000 : 0;
      return h * 3600 + m * 60 + s + milliseconds;
    } catch (error) {
      console.error('Error converting time:', timeStr, error);
      return 0;
    }
  };

  // Handle video time update
  const handleTimeUpdate = (event) => {
    const currentTime = event.target.currentTime;
    const active = subtitles.find(sub => 
      currentTime >= sub.startTime && currentTime <= sub.endTime
    );
    setCurrentSubtitle(active || null);
  };

  // Generate SRT content
  const generateSRTContent = (subtitles) => {
    return subtitles.map((sub, index) => 
      `${index + 1}\n${sub.start} --> ${sub.end}\n${sub.text}\n`
    ).join('\n');
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
            <div className="bg-blue-100 text-blue-700 px-4 py-2 rounded-lg">
              <Video size={16} className="mr-2" />
              Video Localization
            </div>
          </div>
          
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl font-bold mb-6">
              AI-Powered Video Localization
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              Generate accurate subtitles, translate content, and create professional localized videos with advanced AI technology
            </p>
            
            {/* Features badges */}
            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <div className="bg-green-50 text-green-700 px-3 py-1 rounded-lg flex items-center gap-2 text-sm">
                <Video size={16} className="mr-2" />
                HD Video Processing
              </div>
              <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-lg flex items-center gap-2 text-sm">
                <Zap size={16} className="mr-2" />
                Subtitle Generation
              </div>
              <div className="bg-purple-50 text-purple-700 px-3 py-1 rounded-lg flex items-center gap-2 text-sm">
                <Globe size={16} className="mr-2" />
                Multi-language Support
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
          <div className="flex items-center justify-center max-w-5xl mx-auto">
            <div className="flex items-center space-x-4 md:space-x-8">
              {[
                { num: 1, title: 'Upload', icon: Upload },
                { num: 2, title: 'Language', icon: Languages },
                { num: 3, title: 'Process', icon: Video },
                { num: 4, title: 'Download', icon: Download }
              ].map(({ num, title, icon: Icon }, index) => (
                <div key={num} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div className={`w-12 h-12 ${
                      step >= num ? 'bg-green-600 text-white' : 'bg-gray-300 text-gray-600'
                    } rounded-xl flex items-center justify-center font-bold shadow-lg mb-2 transition-all duration-300`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className={`text-sm font-medium ${step >= num ? 'text-green-600' : 'text-gray-500'}`}>
                      {title}
                    </span>
                  </div>
                  {index < 3 && <div className="w-8 md:w-16 h-1 bg-gray-300 rounded-full"></div>}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 flex items-center text-gray-900">
              <Upload className="mr-3 text-green-600" size={28} />
              Upload Video File
            </h2>
            
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-green-500 hover:bg-green-50/30 transition-all duration-300 group">
              <input
                type="file"
                accept=".mp4,.avi,.mov,.webm"
                onChange={handleFileChange}
                className="hidden"
                id="video-upload"
              />
              <label
                htmlFor="video-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
                  <Play className="w-8 h-8 text-green-600" />
                </div>
                <p className="text-lg font-semibold text-gray-700 mb-2">
                  Drop your video file here
                </p>
                <p className=" text-gray-500 mb-4">
                  or click to browse files
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-400">
                  <p>• MP4, AVI, MOV support</p>
                  <p>• WebM format included</p>
                  <p>• Maximum 500MB</p>
                  <p>• HD quality processing</p>
                </div>
              </label>
            </div>

            {file && (
              <div className="mt-8 p-6 bg-green-50 rounded-xl border border-green-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <Video className="w-5 h-5 text-green-600 mr-2" />
                      <p className="font-semibold text-gray-800">{file.name}</p>
                    </div>
                    <p className="text-sm text-gray-500 mb-3">
                      <span className="font-medium">Size:</span> {file.size ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : 'Unknown size'}
                    </p>
                    
                    <div className="flex items-center p-3 bg-green-100 border border-green-300 rounded-lg">
                      <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                      <span className="text-sm font-medium text-green-700">
                        Video file ready for processing
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Language Selection */}
            {step >= 2 && (
              <div className="mt-8 ">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Globe className="w-4 h-4 inline mr-2" />
                  Target Language for Subtitles
                </label>
                <select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select target language...</option>
                  {supportedLanguages.map((lang) => {
                    const code = Array.isArray(lang) ? lang[0] : lang.code;
                    const name = Array.isArray(lang) ? lang[1] : lang.name;
                    return (
                      <option key={code} value={code}>
                        {name} ({code})
                      </option>
                    );
                  })}
                </select>

                <button
                  onClick={handleLocalizeVideo}
                  disabled={!targetLang || isProcessing}
                  className="btn-primary w-full mt-6"
                >
                  {isProcessing ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin mr-2" />
                      {processingStage || 'Processing Video...'}
                    </>
                  ) : (
                    <>
                      <Video className="w-5 h-5 mr-2" />
                      Generate Subtitles
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Results Section */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-8 text-gray-900">
              Localization Results
            </h2>

            {!result && !isProcessing && (
              <div className="text-center py-16">
                <div className="w-20 h-20 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Video className="w-10 h-10 text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Ready for Video Processing</h3>
                <p className=" text-gray-500 max-w-sm mx-auto">
                  Upload a video file and select a target language to generate professional subtitles
                </p>
              </div>
            )}

            {isProcessing && (
              <div className="text-center py-16">
                <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <Loader className="w-8 h-8 text-green-600 animate-spin" />
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Processing Video</h3>
                <p className=" text-gray-600 mb-2">{processingStage}</p>
                <p className="text-sm text-gray-500">This may take several minutes depending on video length</p>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                {/* Video Info */}
                <div className="bg-green-50 border border-green-200 p-6 rounded-xl">
                  <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    Video Information
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600 font-medium">Duration:</span>
                      <span className="font-semibold text-gray-800">{result.duration}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 font-medium">Language:</span>
                      <span className="font-semibold text-gray-800">{result.target_language}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 font-medium">Confidence:</span>
                      <span className="font-semibold text-green-600">{(result.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 font-medium">Status:</span>
                      <span className="font-semibold text-green-600">{result.status}</span>
                    </div>
                  </div>
                </div>

                {/* Video Player Section */}
                {result.video_with_subtitles && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                      Video Preview
                    </h3>
                    <div className="bg-gray-900 rounded-xl overflow-hidden shadow-lg">
                      {!videoUrl && !isVideoLoading && (
                        <div className="aspect-video bg-gray-800 flex items-center justify-center">
                          <button
                            onClick={() => loadVideoForPlayback(result.video_with_subtitles.filename)}
                            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center shadow-md"
                          >
                            <Play className="w-5 h-5 mr-2" />
                            Load Video Preview
                          </button>
                        </div>
                      )}
                      
                      {isVideoLoading && (
                        <div className="aspect-video bg-gray-800 flex items-center justify-center">
                          <div className="text-white text-center">
                            <Loader className="w-8 h-8 mx-auto mb-4 animate-spin text-green-400" />
                            <p className="text-lg font-medium">Loading video...</p>
                          </div>
                        </div>
                      )}
                      
                      {videoUrl && (
                        <div className="relative">
                          <video
                            className="w-full aspect-video"
                            controls
                            onTimeUpdate={handleTimeUpdate}
                            onLoadedData={() => {
                              if (result.subtitle_content) {
                                loadSubtitles(null, result.subtitle_content);
                              } else if (result.subtitles_file) {
                                loadSubtitles(result.subtitles_file.filename);
                              }
                            }}
                          >
                            <source src={videoUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                          </video>
                          
                          {/* Current Subtitle Display */}
                          {currentSubtitle && (
                            <div className="absolute bottom-12 left-0 right-0 px-4">
                              <div className="bg-black bg-opacity-80 text-white p-3 rounded-lg text-center shadow-lg">
                                <p className="text-sm font-medium">{currentSubtitle.text}</p>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Subtitle Display */}
                {subtitles.length > 0 && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                      <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                      Generated Subtitles
                    </h3>
                    <div className="bg-gray-50 border border-gray-200 p-6 rounded-xl max-h-64 overflow-y-auto">
                      {subtitles.map((subtitle, index) => (
                        <div 
                          key={index} 
                          className={`mb-3 p-4 rounded-lg border-l-4 transition-all duration-300 ${
                            currentSubtitle && currentSubtitle.index === subtitle.index
                              ? 'bg-green-100 border-green-500 shadow-md'
                              : 'bg-white border-gray-300 hover:border-gray-400'
                          }`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {subtitle.start} → {subtitle.end}
                            </span>
                          </div>
                          <p className="text-sm text-gray-800 font-medium leading-relaxed">{subtitle.text}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Download Files */}
                <div>
                  <h3 className="text-lg font-bold text-gray-700 mb-4 flex items-center">
                    <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                    Download Files
                  </h3>
                  <div className="space-y-3">
                    {result.subtitles_file && (
                      <div className="bg-gray-50 border border-gray-200 p-4 rounded-xl flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-gray-800">Subtitle File (.srt)</p>
                          <p className="text-sm text-gray-500">{result.subtitles_file.filename}</p>
                        </div>
                        <button
                          onClick={() => handleDownloadVideo(result.subtitles_file.filename)}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center shadow-md"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </button>
                      </div>
                    )}
                    
                    {result.video_with_subtitles && (
                      <div className="bg-gray-50 border border-gray-200 p-4 rounded-xl flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-gray-800">Video with Embedded Subtitles</p>
                          <p className="text-sm text-gray-500">{result.video_with_subtitles.filename}</p>
                        </div>
                        <button
                          onClick={() => handleDownloadVideo(result.video_with_subtitles.filename)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center shadow-md"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download Video
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoLocalization;


