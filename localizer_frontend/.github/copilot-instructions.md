# FRONTEND DEVELOPMENT PROMPT

You are an expert React + Tailwind developer.  
Build a clean, production-ready frontend for:

> **AI-Powered Multilingual Content Localization Engine**  
> Problem Statement ID: 25203  
> Team: SafeHorizon | Smart India Hackathon 2025  

---

## GOAL
Create a simple, professional website that demonstrates AI localization capabilities.  
Show working demos for text, audio, video translation, and LMS/NCVET/MSDE integrations.  
No fancy animations, no monitoring, no testing modules — just functional clarity.

---

## PAGES TO BUILD

### 1. Home Page
- Title and tagline: “AI-Powered Multilingual Content Localization Engine”.
- Buttons to:
  - Document Translation
  - Audio Localization
  - Video Localization
  - LMS / NCVET / MSDE Integration
  - About

---

### 2. Document Translation Page
**Purpose:** Upload → Translate → View/Download.

**Elements:**
- File upload box (`.txt`, `.pdf`, `.docx`)
- Auto Detect Language → `/detect-language`
- Target Language dropdown → `/supported-languages`
- Translate → `/translate`
- Display: Original text, Translated text, Confidence, Download

**APIs:**  
`/content/upload`, `/detect-language`, `/supported-languages`, `/translate`

---

### 3. Audio Localization Page
**Purpose:** Translate speech to another language.

**Elements:**
- Upload audio (`.mp3`, `.wav`)
- Target language dropdown
- Translate Audio → `/speech/translate`
- Play and download result → `/speech/download/{filename}`

**APIs:**  
`/speech/translate`, `/speech/download/{filename}`

---

### 4. Video Localization Page
**Purpose:** Generate subtitles or dubbed video.

**Elements:**
- Upload `.mp4`
- Target language dropdown
- Generate Subtitles → `/video/localize`
- Video preview with subtitles
- Download → `/video/download/{filename}`

**APIs:**  
`/video/localize`, `/video/download/{filename}`

---

### 5. LMS / NCVET / MSDE Integration Page
**Purpose:** Show API integration with CURL-style demos.

**Sections:**

#### A. Upload to Platform
Upload localized file and choose platform (LMS / NCVET / MSDE).  
Trigger → `/integration/upload`

Show CURL:
```bash
curl -X POST https://api.safehorizon.in/integration/upload \
  -F "file=@demo_book_hindi.pdf" \
  -F "target_language=hi" \
  -F "partner=NCVET"
````

Show demo JSON:

```json
{"job_id":"NCVET_1234","status":"Uploaded","message":"File sent to NCVET."}
```

#### B. Check Status

Trigger → `/integration/status`
Display live JSON response.

#### C. Download Result

Trigger → `/integration/download/{job_id}/{language}/{filename}`
Show CURL and result message.

**APIs:**
`/integration/upload`, `/integration/status`, `/integration/download/{job_id}/{language}/{filename}`

---

### 6. About Page

**Purpose:** Explain the project.

Sections:

* Problem Statement (PS 25203)
* Solution overview
* Supported 22 languages (from `/supported-languages`)
* Tech Stack: React, FastAPI, Whisper, IndicTrans2
* Team SafeHorizon
* Smart India Hackathon 2025 acknowledgment

---

## TECH STACK

* React + TailwindCSS
* Axios for API calls
* React Router DOM for navigation
* Lucide-react icons
* Fonts: Poppins / Inter
* Deployment: Vercel or Netlify

---

## DESIGN

* White background, Skill India blue highlights (#004aad)
* Clean card layout
* Simple rounded buttons
* Responsive grid/flex design
* No animations, focus on clarity

---

## DEMO FILES

Place under `/public/demo-assets/`:

* `demo_book_english.pdf`
* `demo_book_hindi.pdf`
* `demo_audio.mp3`
* `demo_video.mp4`

---

## EVALUATOR FLOW

1. Home → Intro
2. Document → File Upload → Translate
3. Audio → Upload → Hear Output
4. Video → Upload → Subtitles
5. Integration → Run CURL-style demos
6. About → Context & Team Info