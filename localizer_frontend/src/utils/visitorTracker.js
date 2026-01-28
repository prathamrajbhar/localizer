// Advanced visitor tracking service

// Get visitor's IP address and location
const getVisitorIP = async () => {
  try {
    const response = await fetch('https://api.ipify.org?format=json');
    const data = await response.json();
    return data.ip;
  } catch (error) {
    console.error('Failed to get IP address:', error);
    return 'Unknown';
  }
};

// Get visitor's location using IP geolocation
const getVisitorLocation = async (ip) => {
  try {
    if (ip === 'Unknown') return null;
    
    const response = await fetch(`https://ipapi.co/${ip}/json/`);
    const data = await response.json();
    
    if (data.error) {
      console.error('IP geolocation error:', data.reason);
      return null;
    }
    
    return {
      city: data.city || 'Unknown',
      region: data.region || 'Unknown',
      country: data.country_name || 'Unknown',
      countryCode: data.country_code || 'Unknown',
      latitude: data.latitude,
      longitude: data.longitude,
      timezone: data.timezone || 'Unknown',
      isp: data.org || 'Unknown',
      postal: data.postal || 'Unknown'
    };
  } catch (error) {
    console.error('Failed to get location:', error);
    return null;
  }
};

// Get browser geolocation (requires user permission)
const getBrowserLocation = () => {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          source: 'browser'
        });
      },
      (error) => {
        console.log('Browser geolocation denied or failed:', error.message);
        resolve(null);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  });
};

// Get additional visitor information
const getAdvancedVisitorInfo = async () => {
  const basicInfo = {
    timestamp: new Date().toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }),
    userAgent: navigator.userAgent,
    language: navigator.language,
    platform: navigator.platform,
    screenResolution: `${window.screen.width}x${window.screen.height}`,
    referrer: document.referrer || 'Direct visit',
    url: window.location.href,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    cookieEnabled: navigator.cookieEnabled,
    onlineStatus: navigator.onLine,
    connectionType: navigator.connection?.effectiveType || 'Unknown',
    memory: navigator.deviceMemory || 'Unknown',
    cores: navigator.hardwareConcurrency || 'Unknown'
  };

  // Get IP address
  const ip = await getVisitorIP();
  basicInfo.ipAddress = ip;

  // Get location data (IP-based)
  const ipLocation = await getVisitorLocation(ip);
  basicInfo.ipLocation = ipLocation;

  // Try to get browser geolocation (more accurate but requires permission)
  const browserLocation = await getBrowserLocation();
  basicInfo.browserLocation = browserLocation;

  return basicInfo;
};

// Track page views and user interactions
export const trackPageView = async (pageName) => {
  try {
    const visitorInfo = await getAdvancedVisitorInfo();
    console.log(`✅ Page view tracked: ${pageName}`, visitorInfo);
  } catch (error) {
    console.error('❌ Failed to track page view:', error);
  }
};

// Track user interactions (button clicks, form submissions, etc.)
export const trackUserAction = async (action, details = '') => {
  try {
    const visitorInfo = await getAdvancedVisitorInfo();
    console.log(`✅ User action tracked: ${action}`, visitorInfo);
  } catch (error) {
    console.error('❌ Failed to track user action:', error);
  }
};

// Track file uploads
export const trackFileUpload = async (fileType, fileName, fileSize) => {
  try {
    const visitorInfo = await getAdvancedVisitorInfo();
    console.log(`✅ File upload tracked: ${fileName}`, visitorInfo);
  } catch (error) {
    console.error('❌ Failed to track file upload:', error);
  }
};

// Track translation requests
export const trackTranslation = async (sourceLang, targetLang, contentType) => {
  try {
    const visitorInfo = await getAdvancedVisitorInfo();
    console.log(`✅ Translation tracked: ${sourceLang} → ${targetLang}`, visitorInfo);
  } catch (error) {
    console.error('❌ Failed to track translation:', error);
  }
};

const visitorTracker = {
  trackPageView,
  trackUserAction,
  trackFileUpload,
  trackTranslation
};

export default visitorTracker;
