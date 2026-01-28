// File validation utilities
export const validateFile = (file, allowedExtensions = [], maxSizeInMB = 10) => {
  if (!file) {
    return { isValid: false, error: 'No file selected' };
  }

  // Check file size
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  if (file.size > maxSizeInBytes) {
    return { isValid: false, error: `File size must be less than ${maxSizeInMB}MB` };
  }

  // Check file extension
  if (allowedExtensions.length > 0) {
    const fileExtension = file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(fileExtension)) {
      return { isValid: false, error: `File must be one of: ${allowedExtensions.map(ext => `.${ext}`).join(', ')}` };
    }
  }

  return { isValid: true, error: null };
};

// Format file size
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Get file extension
export const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase();
};