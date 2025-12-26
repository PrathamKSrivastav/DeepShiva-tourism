# Deep Shiva

## Overview

Deep Shiva is a full-stack system with a FastAPI backend and React (Vite) frontend that combines:

- **Retrieval-Augmented Generation (RAG)** using ChromaDB (local) with optional Qdrant Cloud
- **LLM generation** via Groq API, with a local GGUF fallback
- **Google OAuth authentication**
- **Text-to-Speech** using Kokoro
- **Yoga pose detection and validation** using MediaPipe over WebSockets

This README documents how to set up, run, and inspect the system using only what exists in the repository.

---

## Prerequisites

- Python 3.10 (or compatible)
- Node.js + npm
- Recommended: Docker & docker-compose (optional)

---

## Getting Started

### Backend (Local)

Create and activate virtual environment (Windows example)
python -m venv .venv
.venv\Scripts\activate

Install dependencies
pip install -r backend/requirements.txt

Run backend (from repo root or backend/)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

OR
python main.py


### Frontend (Local)

cd frontend
npm install
npm run dev


Frontend runs on Vite (default port 5173) and expects the backend at `VITE_API_BASE_URL`.

### Docker (Backend + Frontend)

cd docker
docker compose up --build


**Exposed ports:**
- Backend: `8000`
- Frontend: `5173`

---

## Configuration

### Environment Variables

Create a `.env` file manually (not included in repo).

#### Core Settings

MONGODB_URI=mongodb://localhost:27017/deepshiva_tourism

JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars

JWT_ALGORITHM=HS256

JWT_EXPIRY_HOURS=168

ADMIN_EMAILS=comma,separated,emails

FRONTEND_URL=http://localhost:5173

GOOGLE_CLIENT_ID=

GOOGLE_CLIENT_SECRET=


#### Groq / RAG / Vector DB

GROQ_API_KEY= # optional (offline fallback if missing)

GROQ_MODEL=moonshotai/kimi-k2-instruct-0905

GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=800
API_TIMEOUT_SECONDS=120

QDRANT_HOST=
QDRANT_API_KEY=
QDRANT_DIM=384


#### Third-party Tools / Tests

LITEAPI_KEY=
CALLENDRIFIC_API_KEY=
KAGGLE_USERNAME=
KAGGLE_KEY=



#### Frontend (Vite)

VITE_API_BASE_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=


---

## Usage

### Data Ingestion / RAG

cd backend
python scripts/ingest_all_data.py
python scripts/ingest_all_data_local_only.py
python scripts/csv_ingest.py
python scripts/ingest_special_jsons.py


### API Access

After starting the backend:

- **Swagger UI:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

### Tests

python backend/tests/test_llm_with_tool.py
python backend/tests/test_hotel_api.py


**Note:** Several tests require external API keys. Missing keys will cause tests to exit early.

---

## Repository Structure

### Key Paths

├── backend/                      # FastAPI backend application
│   ├── routers/                  # API route definitions
│   │   ├── auth.py               # Google OAuth + JWT authentication
│   │   ├── chat.py               # Chat endpoints (RAG + LLM)
│   │   ├── rag_admin.py          # RAG ingestion & admin APIs
│   │   ├── yoga.py               # Yoga pose detection + WebSocket streaming
│   │   └── tts.py                # Kokoro Text-to-Speech pipeline
│   ├── scripts/                  # Ingestion, debugging, maintenance scripts
│   ├── main.py                   # FastAPI app entry point
│   └── requirements.txt          # Backend dependencies
│
├── frontend/                     # React + Vite single-page application
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── vector_db/                    # Local ChromaDB persistence
├── json_content/                 # RAG JSON data sources
├── spiritual/                    # Spiritual / domain-specific RAG content
├── rag_content/                  # Additional RAG documents
│
├── docker-compose.yml             # Docker orchestration
├── backend.Dockerfile             # Backend container build
│
├── Llama-3.2-1B-Instruct-Q4_K_M.gguf  # Local fallback LLM (offline inference)
└── README.md                      # Project documentation



---

## Architecture

### Frontend

- React + Vite SPA
- Handles Google OAuth client-side
- Communicates with backend via `VITE_API_BASE_URL`

### Backend

- `main.py` — App initialization and router mounting
- `auth.py` — Google OAuth verification, JWT handling
- `chat.py` — Chat endpoints (RAG + LLM)
- `rag_admin.py` — RAG ingestion and admin APIs
- `yoga.py` — Pose detection & WebSocket streaming
- `tts.py` — Kokoro TTS pipeline

### RAG

- `vector_store.py` — ChromaDB (local) with optional Qdrant Cloud
- `rag/content_manager.py` — JSON/PDF ingestion
- `rag/persona_rag.py` — Persona-aware retrieval

### LLM / Generation

- `groq_service.py` — Groq API wrapper + RAG integration
- `local_llm_service.py`, `llm_engine.py` — Local GGUF fallback via llama_cpp

### Data Flow (High-Level)

Frontend
→ Backend API
→ RAG Retrieval (Chroma/Qdrant)
→ Groq API OR Local LLM
→ Response
→ Optional TTS
→ Audio served via /audio or streaming response



---

## API Overview

### Selected Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root (basic feature listing) |
| `/docs` | GET | Swagger UI |
| `/health` | GET | Service health |
| `/api/auth/google` | POST | Google OAuth login |
| `/api/tts/kokoro` | GET | Kokoro TTS |
| `/api/yoga/ws` | WS | Real-time yoga pose analysis |
| `/api/chat/*` | POST | Chat & RAG endpoints |
| `/api/rag/*` | POST | RAG admin and ingestion APIs |

---

## Limitations & Known Gaps

- No LICENSE file present
- No `.env.example` file; environment variables must be created manually
- Groq health-check internals appear incomplete/commented in `groq_service.py`
- Local LLM fallback requires llama_cpp and sufficient system resources
- Tests and tools depend on external API keys
- No CI/CD pipeline or deployment scripts included
- Docker setup is Linux-based; Windows users may prefer Docker or require additional setup
- Static media paths (`/audio`, `/images`) are expected; missing files are logged at runtime

---

## Notes

This README reflects only what is currently implemented in the repository. No future features or assumptions are documented.


