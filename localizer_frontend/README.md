# 🎨 Localizer Frontend

<div align="center">

![React](https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![React Router](https://img.shields.io/badge/React_Router-7.9-CA4245?style=for-the-badge&logo=react-router&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-1.12-5A29E4?style=for-the-badge&logo=axios&logoColor=white)

**Modern, responsive React frontend for the AI-powered multilingual localization platform**

</div>

---

## 📖 Overview

The Localizer frontend is a modern, intuitive web application built with React 19 and TailwindCSS. It provides a seamless user experience for document translation, audio localization, video processing, and platform integration with real-time progress tracking and beautiful UI/UX.

---

## ✨ Features

### 🎯 Core Features

- **📄 Document Translation**: Drag-and-drop interface for PDF, DOCX, TXT files
- **🎙️ Audio Localization**: Audio upload with real-time transcription and voice synthesis
- **🎬 Video Localization**: Video processing with subtitle generation and dubbing options
- **🔗 LMS Integration**: Platform connectivity with educational systems
- **📊 Real-time Progress**: Live status updates with progress bars
- **🌍 Language Selection**: 22+ Indian languages with intuitive selection
- **📱 Responsive Design**: Mobile-first approach, works on all devices

### 💎 UI/UX Features

- **Modern Design**: Clean, professional interface with gradient accents
- **Dark Mode Ready**: Prepared for dark theme implementation
- **Accessibility**: WCAG 2.1 AA compliant
- **Animations**: Smooth transitions and loading states
- **Error Handling**: User-friendly error messages with recovery options
- **File Preview**: Inline preview for uploaded content

---

## 🚀 Getting Started

### Prerequisites

- **Node.js**: 16.x or higher
- **npm**: 8.x or higher (or yarn 1.22+)
- **Backend**: Localizer backend running on http://localhost:8000

### Installation

#### 1️⃣ Navigate to Frontend Directory

```bash
cd localizer_frontend
```

#### 2️⃣ Install Dependencies

```bash
# Using npm
npm install

# Using yarn
yarn install
```

#### 3️⃣ Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# nano .env  # or use your preferred editor
```

**Sample `.env` configuration:**

```env
# Backend API URL
REACT_APP_API_URL=http://localhost:8000

# File Upload Settings
REACT_APP_MAX_FILE_SIZE=104857600  # 100MB in bytes
REACT_APP_SUPPORTED_FORMATS=pdf,docx,txt,mp3,wav,mp4,avi,mov

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_VISITOR_TRACKING=true

# API Timeouts (milliseconds)
REACT_APP_API_TIMEOUT=300000  # 5 minutes

# UI Settings
REACT_APP_THEME=light
REACT_APP_LANGUAGE=en
```

#### 4️⃣ Start Development Server

```bash
# Using npm
npm start

# Using yarn
yarn start
```

The application will open at http://localhost:3000

#### 5️⃣ Build for Production

```bash
# Using npm
npm run build

# Using yarn
yarn build

# Output will be in the 'build' directory
```

---

## 📁 Project Structure

```
localizer_frontend/
├── public/                     # Static assets
│   ├── index.html              # HTML template
│   ├── manifest.json           # PWA manifest
│   ├── robots.txt              # SEO robots file
│   └── favicon.ico             # Favicon
├── src/
│   ├── components/             # Reusable components
│   │   ├── Layout.js           # Main layout wrapper
│   │   └── Navbar.js           # Navigation component
│   ├── pages/                  # Page components
│   │   ├── Home.js             # Landing page
│   │   ├── DocumentTranslation.js  # Document upload/translation
│   │   ├── AudioLocalization.js    # Audio processing
│   │   ├── VideoLocalization.js    # Video processing
│   │   ├── Integration.js          # LMS integration
│   │   └── About.js                # About page
│   ├── utils/                  # Utility functions
│   │   ├── apiService.js       # API client with Axios
│   │   ├── constants.js        # App constants (languages, etc.)
│   │   ├── fileUtils.js        # File handling utilities
│   │   └── visitorTracker.js   # Analytics tracking
│   ├── App.js                  # Main App component
│   ├── App.css                 # Global styles
│   ├── index.js                # Entry point
│   ├── index.css               # TailwindCSS imports
│   └── reportWebVitals.js      # Performance monitoring
├── .env                        # Environment variables
├── package.json                # Dependencies and scripts
├── tailwind.config.js          # TailwindCSS configuration
├── postcss.config.js           # PostCSS configuration
└── README.md                   # This file
```

---

## 🎨 Component Architecture

### Component Hierarchy

```
App
├── Layout
│   ├── Navbar
│   └── {children}
│       ├── Home
│       ├── DocumentTranslation
│       ├── AudioLocalization
│       ├── VideoLocalization
│       ├── Integration
│       └── About
```

### Key Components

#### 1. **Navbar**
```jsx
// Navigation with active route highlighting
<Navbar />
```
- Responsive design
- Mobile hamburger menu
- Active route indication

#### 2. **Layout**
```jsx
// Wrapper for all pages
<Layout>
  <YourPage />
</Layout>
```
- Consistent page structure
- Navbar integration
- Footer (optional)

#### 3. **DocumentTranslation**
```jsx
// Document upload and translation
<DocumentTranslation />
```
- Drag-and-drop file upload
- Language selection
- Real-time progress tracking
- Download translated file

#### 4. **AudioLocalization**
```jsx
// Audio processing interface
<AudioLocalization />
```
- Audio file upload
- Transcription display
- Translation controls
- Audio playback

#### 5. **VideoLocalization**
```jsx
// Video processing interface
<VideoLocalization />
```
- Video upload
- Subtitle generation
- Dubbing options
- Video preview

---

## 🔌 API Integration

### API Service Structure

```javascript
// src/utils/apiService.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Example endpoints
export const translateDocument = (formData) => {
  return apiClient.post('/api/translation/translate-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const getSupportedLanguages = () => {
  return apiClient.get('/api/translation/languages');
};
```

### Supported API Calls

| Function | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| `translateDocument()` | `/api/translation/translate-file` | POST | Upload and translate document |
| `translateText()` | `/api/translation/translate` | POST | Translate text directly |
| `transcribeAudio()` | `/api/speech/transcribe` | POST | Audio to text |
| `synthesizeSpeech()` | `/api/speech/synthesize` | POST | Text to speech |
| `generateSubtitles()` | `/api/video/generate-subtitles` | POST | Video subtitle generation |
| `dubVideo()` | `/api/video/dub` | POST | Video dubbing |
| `getSupportedLanguages()` | `/api/translation/languages` | GET | Get language list |
| `getSystemHealth()` | `/health/detailed` | GET | System status |

---

## 🎨 Styling

### TailwindCSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4A90E2',
        secondary: '#7B68EE',
        accent: '#50C878',
        danger: '#FF6B6B',
      },
      fontFamily: {
        sans: ['Inter', 'Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

### Custom CSS

```css
/* src/index.css */
@import '@fontsource/inter';
@import '@fontsource/poppins';

@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom utility classes */
@layer components {
  .btn-primary {
    @apply bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow;
  }
}
```

---

## 📱 Responsive Design

### Breakpoints

```javascript
// TailwindCSS default breakpoints
sm: '640px'   // Mobile landscape
md: '768px'   // Tablet
lg: '1024px'  // Desktop
xl: '1280px'  // Large desktop
2xl: '1536px' // Extra large
```

### Mobile-First Approach

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Responsive grid: 1 column on mobile, 2 on tablet, 3 on desktop */}
</div>
```

---

## 🧪 Testing

### Run Tests

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

### Test Structure

```javascript
// Example test
import { render, screen } from '@testing-library/react';
import Home from './pages/Home';

test('renders home page', () => {
  render(<Home />);
  const element = screen.getByText(/Welcome to Localizer/i);
  expect(element).toBeInTheDocument();
});
```

---

## 🚀 Deployment

### Build for Production

```bash
# Create optimized production build
npm run build

# Output will be in 'build' directory
# - Minified JavaScript
# - Optimized CSS
# - Compressed assets
```

### Deploy to Static Hosting

#### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

#### Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod
```

#### Traditional Hosting
```bash
# Build the app
npm run build

# Upload the 'build' directory to your web server
# Configure web server to serve index.html for all routes
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/localizer-frontend/build;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API base URL | `http://localhost:8000` |
| `REACT_APP_MAX_FILE_SIZE` | Max file upload size (bytes) | `104857600` (100MB) |
| `REACT_APP_SUPPORTED_FORMATS` | Allowed file formats | `pdf,docx,txt,mp3,wav,mp4` |
| `REACT_APP_API_TIMEOUT` | API request timeout (ms) | `300000` (5 min) |
| `REACT_APP_ENABLE_ANALYTICS` | Enable visitor tracking | `false` |

---

## 🎯 Performance Optimization

### Code Splitting

```javascript
// Lazy load pages
import { lazy, Suspense } from 'react';

const DocumentTranslation = lazy(() => import('./pages/DocumentTranslation'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DocumentTranslation />
    </Suspense>
  );
}
```

### Image Optimization

```jsx
// Use modern image formats
<img 
  src="image.webp" 
  alt="Description" 
  loading="lazy" 
  className="w-full h-auto"
/>
```

### Bundle Analysis

```bash
# Analyze bundle size
npm install --save-dev source-map-explorer
npm run build
npx source-map-explorer 'build/static/js/*.js'
```

---

## 🔒 Security

### Best Practices Implemented

- ✅ **XSS Prevention**: React's built-in escaping
- ✅ **CSRF Protection**: Token-based authentication (if enabled)
- ✅ **Secure Headers**: CSP, X-Frame-Options
- ✅ **Input Validation**: Client-side validation before API calls
- ✅ **Environment Variables**: No secrets in code
- ✅ **HTTPS Only**: Force HTTPS in production

---

## 📊 Analytics & Monitoring

### Visitor Tracking

```javascript
// src/utils/visitorTracker.js
export const trackPageView = (pageName) => {
  if (process.env.REACT_APP_ENABLE_ANALYTICS === 'true') {
    // Track page view
    console.log(`Page view: ${pageName}`);
  }
};
```

### Performance Monitoring

```javascript
// src/reportWebVitals.js
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

const sendToAnalytics = (metric) => {
  // Send to analytics service
  console.log(metric);
};

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

---

## 🤝 Contributing

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Frontend-specific Guidelines

1. **Component Structure**: Use functional components with hooks
2. **Styling**: TailwindCSS utility-first approach
3. **State Management**: React hooks (useState, useEffect, etc.)
4. **Code Formatting**: Use Prettier
5. **Linting**: Follow ESLint rules

---

## 📄 License

MIT License - see [../LICENSE](../LICENSE)

---

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/prathamrajbhar/localizer/issues)
- **Email**: frontend-support@localizer.ai (placeholder)
- **Docs**: [Main README](../README.md)

---

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [TailwindCSS Docs](https://tailwindcss.com/docs)
- [React Router Docs](https://reactrouter.com/)
- [Axios Documentation](https://axios-http.com/docs/intro)

---

<div align="center">

**Built with React ⚛️ | Styled with Tailwind 🎨 | Made with ❤️ by Team SafeHorizon**

[⬆ Back to Top](#-localizer-frontend)

</div>
