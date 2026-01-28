// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  TIMEOUT: 0, // No timeout for audio processing
  MAX_FILE_SIZE: 500 * 1024 * 1024, // 500MB for audio files
  SUPPORTED_FORMATS: {
    document: ['.txt', '.pdf', '.docx', '.doc', '.rtf'],
    audio: ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'],
    video: ['.mp4', '.avi', '.mov', '.webm'],
    assessment: ['.json', '.csv']
  },
  AUDIO_CONFIG: {
    MAX_DURATION: 3600, // 1 hour maximum
    MIN_DURATION: 1, // 1 second minimum
    SUPPORTED_SAMPLE_RATES: [8000, 16000, 22050, 44100, 48000],
    SUPPORTED_BIT_DEPTHS: [16, 24, 32],
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 2000 // 2 seconds
  }
};

// Supported languages (22 Indian languages)
export const DEFAULT_LANGUAGES = [
  { code: 'as', name: 'Assamese' },
  { code: 'bn', name: 'Bengali' },
  { code: 'brx', name: 'Bodo' },
  { code: 'doi', name: 'Dogri' },
  { code: 'gu', name: 'Gujarati' },
  { code: 'hi', name: 'Hindi' },
  { code: 'kn', name: 'Kannada' },
  { code: 'ks', name: 'Kashmiri' },
  { code: 'kok', name: 'Konkani' },
  { code: 'mai', name: 'Maithili' },
  { code: 'ml', name: 'Malayalam' },
  { code: 'mni', name: 'Manipuri' },
  { code: 'mr', name: 'Marathi' },
  { code: 'ne', name: 'Nepali' },
  { code: 'or', name: 'Odia' },
  { code: 'pa', name: 'Punjabi' },
  { code: 'sa', name: 'Sanskrit' },
  { code: 'sat', name: 'Santali' },
  { code: 'sd', name: 'Sindhi' },
  { code: 'ta', name: 'Tamil' },
  { code: 'te', name: 'Telugu' },
  { code: 'ur', name: 'Urdu' }
];


// Platform integration data
export const SUPPORTED_PLATFORMS = [
  { id: 'ncvet', name: 'NCVET', description: 'National Council for Vocational Education and Training' },
  { id: 'msde', name: 'MSDE', description: 'Ministry of Skill Development and Entrepreneurship' },
  { id: 'lms', name: 'LMS', description: 'Learning Management System' }
];