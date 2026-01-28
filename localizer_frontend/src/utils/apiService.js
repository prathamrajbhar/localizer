import axios from 'axios';
import { API_CONFIG } from './constants';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// File upload helper
const createFormData = (file, additionalData = {}) => {
  const formData = new FormData();
  formData.append('file', file);
  
  Object.keys(additionalData).forEach(key => {
    if (additionalData[key] !== undefined && additionalData[key] !== null) {
      formData.append(key, additionalData[key]);
    }
  });
  
  return formData;
};

// API Services
export const apiService = {
  // Health & System
  async checkHealth() {
    const response = await api.get('/');
    return response.data;
  },

  async getDetailedHealth() {
    const response = await api.get('/health/detailed');
    return response.data;
  },

  async getSystemInfo() {
    const response = await api.get('/system/info');
    return response.data;
  },

  // Language Services
  async getSupportedLanguages() {
    const response = await api.get('/supported-languages');
    return response.data;
  },

  async detectLanguage(textOrObject) {
    const payload = typeof textOrObject === 'string' 
      ? { text: textOrObject }
      : textOrObject;
    
    const response = await api.post('/detect-language', payload);
    return response.data;
  },

  // Content Management
  async uploadFile(file, domain = 'general', sourceLanguage = 'en') {
    const formData = createFormData(file, { 
      domain, 
      source_language: sourceLanguage 
    });
    
    const response = await api.post('/content/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async listFiles(skip = 0, limit = 10) {
    const response = await api.get(`/content/files?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  async getFileDetails(fileId) {
    const response = await api.get(`/content/files/${fileId}`);
    return response.data;
  },

  async deleteFile(fileId) {
    await api.delete(`/content/files/${fileId}`);
  },

  // Simple upload endpoint
  async uploadContent(file) {
    const formData = createFormData(file);
    
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Translation Services
  async translateText(params) {
    // Handle both old and new API signatures
    let payload;
    
    if (typeof params === 'string') {
      // Old signature: translateText(text, sourceLanguage, targetLanguages, ...)
      const [text, sourceLanguage, targetLanguages, domain = 'general', applyLocalization = true] = arguments;
      payload = {
        text,
        source_language: sourceLanguage,
        target_languages: Array.isArray(targetLanguages) ? targetLanguages : [targetLanguages],
        domain,
        apply_localization: applyLocalization
      };
    } else {
      // New signature: translateText({ text, source_language, target_language(s), ... }) or ({ file_id, source_language, target_language(s), ... })
      payload = {
        source_language: params.source_language,
        target_languages: Array.isArray(params.target_languages) 
          ? params.target_languages 
          : [params.target_language || params.target_languages],
        domain: params.domain || 'general',
        apply_localization: params.apply_localization !== undefined ? params.apply_localization : true
      };
      
      // Add either text or file_id based on what's provided
      if (params.file_id) {
        payload.file_id = params.file_id;
      } else if (params.text) {
        payload.text = params.text;
      }
    }
    
    const response = await api.post('/translate', payload);
    return response.data;
  },

  async translateFile(fileId, sourceLanguage, targetLanguages, domain = 'general', applyLocalization = true) {
    const response = await api.post('/translate', {
      file_id: fileId,
      source_language: sourceLanguage,
      target_languages: Array.isArray(targetLanguages) ? targetLanguages : [targetLanguages],
      domain,
      apply_localization: applyLocalization
    });
    return response.data;
  },

  // Speech Processing
  async speechToText(audioFile, language = 'auto') {
    const formData = createFormData(audioFile, { language });
    
    const response = await api.post('/speech/stt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async textToSpeech(text, language, voiceSpeed = 1.0, outputFormat = 'mp3') {
    const response = await api.post('/speech/tts', {
      text,
      language,
      voice_speed: voiceSpeed,
      output_format: outputFormat
    });
    return response.data;
  },

  async localizeAudio(audioFile, targetLanguage, domain = 'general', options = {}) {
    const formData = createFormData(audioFile, { 
      target_language: targetLanguage,
      domain,
      ...options
    });
    
    // Create a custom axios instance for audio processing without timeout
    const audioApi = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: 0, // No timeout for audio processing
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    // Add retry logic for audio processing
    let lastError;
    for (let attempt = 1; attempt <= API_CONFIG.AUDIO_CONFIG.RETRY_ATTEMPTS; attempt++) {
      try {
        console.log(`Audio localization attempt ${attempt}/${API_CONFIG.AUDIO_CONFIG.RETRY_ATTEMPTS}`);
        
        const response = await audioApi.post('/speech/localize', formData);
        console.log('Audio localization successful');
        return response.data;
      } catch (error) {
        lastError = error;
        console.warn(`Audio localization attempt ${attempt} failed:`, error.message);
        
        if (attempt < API_CONFIG.AUDIO_CONFIG.RETRY_ATTEMPTS) {
          console.log(`Retrying in ${API_CONFIG.AUDIO_CONFIG.RETRY_DELAY}ms...`);
          await new Promise(resolve => setTimeout(resolve, API_CONFIG.AUDIO_CONFIG.RETRY_DELAY));
        }
      }
    }
    
    throw lastError;
  },

  async generateSubtitles(videoFile, language = 'en', format = 'srt') {
    const formData = createFormData(videoFile, { language, format });
    
    const response = await api.post('/speech/subtitles', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async downloadAudio(filename) {
    const response = await api.get(`/speech/download/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Advanced audio processing methods
  async validateAudioFile(audioFile) {
    return new Promise((resolve, reject) => {
      const audio = new Audio();
      const url = URL.createObjectURL(audioFile);
      
      audio.addEventListener('loadedmetadata', () => {
        URL.revokeObjectURL(url);
        const duration = audio.duration;
        const isValid = duration >= API_CONFIG.AUDIO_CONFIG.MIN_DURATION && 
                       duration <= API_CONFIG.AUDIO_CONFIG.MAX_DURATION;
        
        resolve({
          isValid,
          duration,
          error: isValid ? null : `Audio duration must be between ${API_CONFIG.AUDIO_CONFIG.MIN_DURATION}s and ${API_CONFIG.AUDIO_CONFIG.MAX_DURATION}s`
        });
      });
      
      audio.addEventListener('error', () => {
        URL.revokeObjectURL(url);
        reject(new Error('Invalid audio file format'));
      });
      
      audio.src = url;
    });
  },

  async enhanceAudio(audioFile, options = {}) {
    const formData = createFormData(audioFile, {
      noise_reduction: options.noiseReduction || true,
      volume_normalization: options.volumeNormalization || true,
      echo_cancellation: options.echoCancellation || true,
      ...options
    });
    
    const response = await api.post('/speech/enhance', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 0 // No timeout for audio enhancement
    });
    return response.data;
  },

  async getAudioProcessingStatus(jobId) {
    const response = await api.get(`/speech/status/${jobId}`);
    return response.data;
  },

  async cancelAudioProcessing(jobId) {
    const response = await api.post(`/speech/cancel/${jobId}`);
    return response.data;
  },

  // Video Processing
  async localizeVideo(videoFile, targetLanguage, domain = 'general', includeSubtitles = true, includeDubbedAudio = false, subtitleTargetLanguage = null) {
    const formData = createFormData(videoFile, {
      target_language: targetLanguage,
      domain,
      include_subtitles: includeSubtitles,
      include_dubbed_audio: includeDubbedAudio,
      // Add subtitle target language if specified
      ...(subtitleTargetLanguage && { subtitle_target_language: subtitleTargetLanguage })
    });
    
    const response = await api.post('/video/localize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async extractAudio(videoFile, outputFormat = 'wav') {
    const formData = createFormData(videoFile, { output_format: outputFormat });
    
    const response = await api.post('/video/extract-audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async downloadVideo(filename) {
    const response = await api.get(`/video/download/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Assessment Translation
  async translateAssessment(assessmentFile, targetLanguage, domain = 'education') {
    const formData = createFormData(assessmentFile, {
      target_language: targetLanguage,
      domain
    });
    
    const response = await api.post('/assessment/translate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async validateAssessment(assessmentFile) {
    const formData = createFormData(assessmentFile);
    
    const response = await api.post('/assessment/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async getSampleAssessmentFormats() {
    const response = await api.get('/assessment/sample-formats');
    return response.data;
  },

  async downloadAssessment(filename) {
    const response = await api.get(`/assessment/download/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Job Management
  async getJobStatus(jobId) {
    const response = await api.get(`/jobs/${jobId}`);
    return response.data;
  },

  async listActiveJobs() {
    const response = await api.get('/jobs');
    return response.data;
  },

  async cancelJob(jobId) {
    const response = await api.delete(`/jobs/${jobId}`);
    return response.data;
  },

  // LMS Integration
  async integrationUpload(file, targetLanguages, contentType, domain = 'general', partnerId, priority = 'normal') {
    const formData = createFormData(file, {
      target_languages: Array.isArray(targetLanguages) ? targetLanguages.join(',') : targetLanguages,
      content_type: contentType,
      domain,
      partner_id: partnerId,
      priority
    });
    
    const response = await api.post('/integration/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async getIntegrationResults(jobId) {
    const response = await api.get(`/integration/results/${jobId}`);
    return response.data;
  },

  async getIntegrationStatus() {
    const response = await api.get('/integration/status');
    return response.data;
  },

  async downloadIntegrationOutput(jobId, language, filename) {
    const response = await api.get(`/integration/download/${jobId}/${language}/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  async submitIntegrationFeedback(jobId, partnerId, qualityRating, accuracyRating, comments) {
    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('partner_id', partnerId);
    formData.append('quality_rating', qualityRating);
    formData.append('accuracy_rating', accuracyRating);
    formData.append('feedback_comments', comments);
    
    const response = await api.post('/integration/feedback', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Feedback
  async submitFeedback(rating, comments, fileId = null, accuracyRating = null, culturalAppropriateness = null, corrections = null) {
    const feedbackData = {
      rating,
      comments
    };
    
    if (fileId) feedbackData.file_id = fileId;
    if (accuracyRating) feedbackData.accuracy_rating = accuracyRating;
    if (culturalAppropriateness) feedbackData.cultural_appropriateness = culturalAppropriateness;
    if (corrections) feedbackData.corrections = corrections;
    
    const response = await api.post('/feedback', feedbackData);
    return response.data;
  },

  async listFeedback(skip = 0, limit = 10, translationId = null) {
    let url = `/feedback?skip=${skip}&limit=${limit}`;
    if (translationId) {
      url += `&translation_id=${translationId}`;
    }
    
    const response = await api.get(url);
    return response.data;
  },

  async getFeedback(feedbackId) {
    const response = await api.get(`/feedback/${feedbackId}`);
    return response.data;
  },

  // Statistics
  async getStats() {
    const response = await api.get('/stats');
    return response.data;
  },

  async getTranslationHistory(fileId) {
    const response = await api.get(`/history/${fileId}`);
    return response.data;
  }
};

// Utility functions for file handling
export const fileUtils = {
  validateFile(file, type = 'document') {
    if (!file) {
      throw new Error('No file provided');
    }
    
    const allowedFormats = API_CONFIG.SUPPORTED_FORMATS[type] || [];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (allowedFormats.length > 0 && !allowedFormats.includes(fileExtension)) {
      throw new Error(`Unsupported file format. Allowed formats: ${allowedFormats.join(', ')}`);
    }
    
    if (file.size > API_CONFIG.MAX_FILE_SIZE) {
      throw new Error(`File size exceeds ${API_CONFIG.MAX_FILE_SIZE / (1024 * 1024)}MB limit`);
    }
    
    return true;
  },

  downloadBlob(blob, filename) {
    try {
      if (!blob) {
        throw new Error('No blob data to download');
      }
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      throw new Error('Failed to download file: ' + error.message);
    }
  },

  // Additional API endpoints
  async getPerformanceMetrics() {
    const response = await api.get('/performance');
    return response.data;
  },

  async validateAssessmentFormat(file) {
    const formData = createFormData(file);
    
    const response = await api.post('/assessment/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async translateAssessment(file, targetLanguage, domain = 'education') {
    const formData = createFormData(file, { 
      target_language: targetLanguage,
      domain: domain
    });
    
    const response = await api.post('/assessment/translate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getFileType(filename) {
    const extension = '.' + filename.split('.').pop().toLowerCase();
    
    for (const [type, formats] of Object.entries(API_CONFIG.SUPPORTED_FORMATS)) {
      if (formats.includes(extension)) {
        return type;
      }
    }
    
    return 'unknown';
  }
};

export default api;