# 🌐 WEBSITE BACKEND INTEGRATION IMPLEMENTATION PROMPT

You are an expert full-stack developer.  
Integrate all backend API endpoints of the **AI-Powered Multilingual Content Localization Engine** into the website frontend.

---

## 🎯 GOAL
Connect the frontend UI directly with backend FastAPI endpoints so users can:
- Upload demo content (text, audio, video)
- Run live translation/localization directly from the browser
- View JSON responses, confidence scores, progress status
- Download generated outputs (PDF, MP3, MP4)
- Test LMS / NCVET / MSDE integration end-to-end without terminal commands

---

## 🔌 BACKEND BASE URL
`https://api.safehorizon.in`  
*(replace with localhost during development if needed)*

---

## 🔁 WORKFLOWS TO INTEGRATE

### 1️⃣ Document / Text Translation
- **Endpoints:** `/content/upload`, `/detect-language`, `/translate`
- **Flow:** Upload → Detect Language → Translate → Show output + Download button
- **Frontend UI:** File upload, target language dropdown, translate button, result area.

---

### 2️⃣ Audio Localization
- **Endpoints:** `/speech/localize`, `/speech/download/{filename}`
- **Flow:** Upload → Backend runs STT + Translate + TTS → Show localized audio + Download
- **Frontend UI:** Upload audio → target language select → progress bar → play localized audio.

---

### 3️⃣ Video Localization
- **Endpoints:** `/video/localize`, `/video/download/{filename}`
- **Flow:** Upload → Generate localized subtitles → Preview video with subtitles → Download.
- **Frontend UI:** Upload box, target language select, video preview with `<track>` for subtitles.

---

### 4️⃣ LMS / NCVET / MSDE Integration
- **Endpoints:** `/integration/upload`, `/integration/status`, `/integration/results/{job_id}`, `/integration/download/{job_id}/{language}/{filename}`
- **Flow:**  
  Upload localized file → Show CURL + JSON response → Fetch results → Download outputs.
- **Frontend UI:**  
  - Dropdown for platform (LMS / NCVET / MSDE)  
  - Upload demo file (document/audio/video)  
  - Target language select  
  - Buttons for “Send”, “Check Status”, “Fetch Results”, “Download Output”  
  - Display response JSON in formatted block.

---

## 🧱 UI IMPLEMENTATION GUIDELINES
- Use **React + TailwindCSS** (simple card-based layout, white + blue theme).  
- Keep pages minimal:
  - Home → Overview and Start buttons
  - Translate → Document translation UI
  - Audio → Audio localization UI
  - Video → Video localization UI
  - LMS → Integration tester UI
  - About → Problem statement, team, tech stack
- Always show **real API responses** on screen (formatted JSON).
- Provide **download links** directly from response paths.

---

## ⚙️ FUNCTIONAL REQUIREMENTS
- Use `Axios` for all HTTP requests.  
- Handle async processes with loading spinners.  
- Show toast or banner for API success/failure.  
- Validate file types and sizes before upload.  
- Preload **demo files** (e.g. `demo_book.pdf`, `demo_audio.mp3`, `demo_video.mp4`) for testing.  
- Use `/supported-languages` endpoint to populate language dropdowns.  
- Show job progress (for long video/audio translations) using `job_id`.

---

## ✅ OUTPUT EXPECTATION
A **fully connected website** where evaluators can:
- Upload content and see instant translation/localization results.
- Listen to localized audio, watch localized video with subtitles.
- Test LMS/NCVET/MSDE integration directly in-browser with live API responses.
- Download generated files directly from backend.

The frontend must demonstrate **real working AI functionality** through the backend APIs — no manual steps, no fake data.

---

## 🧭 SUCCESS CRITERIA
- All 4 main workflows (Text, Audio, Video, LMS) run end-to-end.
- Every result (text/audio/video) visible or downloadable on the page.
- LMS/NCVET/MSDE integration shows live request + response flow.
- Clean, simple, production-grade UI — evaluator understands everything at a glance.
