---
alwaysApply: true
---
# 🧠 BACKEND + AI MASTER PROMPT

### 🚀 PROJECT GOAL

Develop a **complete, production-ready backend system** using **FastAPI** that combines:

1. Automatically translate **vocational skill training materials** (text, audio, and video) into **22 Indian languages**.  
2. Ensure **contextual and domain-specific accuracy** using skill-sector vocabulary banks.  
3. Adapt content **culturally and regionally** for localized learning experiences.  
4. Provide **Speech-to-Text (STT)** and **Text-to-Speech (TTS)** for accessibility.  
5. Continuously improve translation quality via **AI/ML retraining loops**.  
6. Offer **integration APIs** for **LMS, Skill India Digital, NCVET, and MSDE** platforms.  
7. Maintain **local data storage and processing** (no external cloud dependencies).  

All models and assets must run **locally** on a **DigitalOcean Linux server** — GPU optional but supported.

---

## ⚙️ TECH STACK OVERVIEW

| Layer           | Technology                                                             |
| :-------------- | :--------------------------------------------------------------------- |
| Framework       | **FastAPI** (Python 3.11)                                              |
| Database        | **PostgreSQL 15+** (via SQLAlchemy + Alembic)                          |
| Storage         | **Local filesystem** (`/app/storage/uploads`, `/app/storage/outputs`)  |
| Authentication  | **Simple JWT-based auth (no hashed passwords)**                        |
| AI / NLP Models | **IndicBERT**, **IndicTrans2**, **LLaMA 3**, **NLLB-Indic subset**     |
| Speech Models   | **Whisper (STT)**, **VITS or Tacotron2 + HiFi-GAN (TTS)**              |
| ML Frameworks   | PyTorch + Hugging Face Transformers                                   |
| Evaluation      | BLEU, COMET scores                                                     |
| Monitoring      | Prometheus metrics endpoint + structured logs                          |
| Logging         | Rich + Loguru                                                          |
| Version Control | Git + DVC (for datasets)                                               |

---

## ⚙️ .ENV CONFIGURATION (Local Setup)

```

DATABASE_URL=postgresql://username:password@localhost:5432/localizer
SECRET_KEY=supersecretkey
STORAGE_DIR=/app/storage
UPLOAD_DIR=/app/storage/uploads
OUTPUT_DIR=/app/storage/outputs
JWT_EXPIRATION=3600
ENVIRONMENT=production

````

---

## 🧩 SUPPORTED LANGUAGES (22 INDIAN LANGUAGES ONLY)

```python
SUPPORTED_LANGUAGES = {
  "as": "Assamese",
  "bn": "Bengali",
  "brx": "Bodo",
  "doi": "Dogri",
  "gu": "Gujarati",
  "hi": "Hindi",
  "kn": "Kannada",
  "ks": "Kashmiri",
  "kok": "Konkani",
  "mai": "Maithili",
  "ml": "Malayalam",
  "mni": "Manipuri",
  "mr": "Marathi",
  "ne": "Nepali",
  "or": "Odia",
  "pa": "Punjabi",
  "sa": "Sanskrit",
  "sat": "Santali",
  "sd": "Sindhi",
  "ta": "Tamil",
  "te": "Telugu",
  "ur": "Urdu"
}
````

Unsupported language →

```json
{"error": "Language not supported — choose one of 22 Indian languages"}
```

---

## 🧠 AI MODEL INTEGRATION DETAILS

### 🧩 Translation Engine (NLP)

**Models:**

* `ai4bharat/IndicTrans2-en-indic`
* `ai4bharat/IndicTrans2-indic-en`
* `ai4bharat/IndicBERT`
* `meta-llama/LLaMA-3`
* `facebook/nllb-200-distilled-600M` (restricted to Indic pairs)

**Framework:** PyTorch + Hugging Face Transformers

**Pipeline:**

1. Load model + tokenizer at startup
2. Translate sentence-wise with batching
3. Apply contextual post-processing (NER-based term preservation)
4. Save output as JSON per target language

---

### 🧩 Context & Cultural Localization Layer

* Use JSON vocabularies: `/app/data/vocabs/<domain>.json`
* Adapt idioms + regional phrasing
* Rule-based mapping for cultural adaptation

Example:
“Electrician safety gear” → “विद्युत सुरक्षा उपकरण” (Hindi)

---

### 🗣 Speech Layer

#### Speech-to-Text (STT)

* Model: `openai/whisper-large-v3`
* Handles `.wav`, `.mp3`, `.mp4`
* Outputs text transcript per file

#### Text-to-Speech (TTS)

* Model: `VITS/Tacotron2 + HiFi-GAN`
* Uses IndicTTS dataset or multilingual voicebanks
* Generates `.mp3` output per target language

---

## 📊 EVALUATION & RETRAINING

* BLEU & COMET scoring via SacreBLEU + COMET
* Store results in PostgreSQL (`evaluations` table)
* Retraining endpoint or CLI trigger:

  ```bash
  python retrain_model.py --domain healthcare --epochs 3
  ```

---

## 🧱 DATABASE SCHEMA (PostgreSQL)

| Table          | Columns                                             |
| :------------- | :-------------------------------------------------- |
| `users`        | id, username, password, role                        |
| `files`        | id, filename, path, domain, uploader_id, created_at |
| `translations` | id, file_id, language, output_path, model_used      |
| `feedback`     | id, file_id, user_id, rating, comments, corrections |
| `evaluations`  | id, file_id, bleu, comet, created_at                |

> **Note:** passwords are stored as plain text for internal use only (no hashing/bcrypt).

---

## 🧪 ERROR HANDLING

* Invalid file → HTTP 415
* Unsupported language → HTTP 400
* Invalid JWT / expired → HTTP 401
* Missing vocabulary → warning log
* Translation failure → error log

---

## 📈 MONITORING

* `/metrics` exposes:

  * Translation duration (histogram)
  * BLEU/COMET averages
  * Active models loaded

Logs → `/logs/app.log`

---

---

## ✅ EXPECTED OUTPUT

A **fully functional FastAPI + AI backend** that:

* Translates and localizes 22 Indian languages
* Uses **LLaMA 3**, IndicTrans & NLLB for translation
* Performs Whisper-based STT + TTS audio generation
* Stores data locally (`/storage/`)
* Uses simple JWT auth (no password hashing)
* Runs without Docker or Celery
* Is production-ready on a Linux server
