# Deep Shiva

Deep Shiva is a full-stack, AI-powered interactive tourism platform designed to provide spiritually and culturally rich travel guidance for India. It is built with a FastAPI backend and a React (Vite) frontend.

It utilizes Retrieval-Augmented Generation (RAG) to serve domain-specific knowledge, features multi-persona AI conversations, integrates real-time yoga pose validation via WebSockets, and offers Text-to-Speech (TTS) capabilities.

---

## 🏗️ Architecture & Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **LLM Engine**: Groq API (e.g., `moonshotai/kimi-k2-instruct-0905`) with an offline fallback using a local quantized model (`Llama-3.2-1B-Instruct-Q4_K_M.gguf`) via `llama_cpp`.
- **RAG & Vector DB**: ChromaDB (local default) with optional Qdrant Cloud integration.
- **Database**: MongoDB for user profiles, auth metadata, and chat histories.
- **Authentication**: Google OAuth 2.0 with JWT.
- **TTS**: Kokoro.
- **Tools / Agentic Workflows**: Integrated functions for live data fetching (Weather, Hotels, Geocoding, Treks, Holidays).

### Frontend
- **Framework**: React 18 + Vite.
- **Styling**: TailwindCSS & custom CSS.
- **3D & Interactivity**: `three.js`, `@react-three/fiber`, and `framer-motion`.
- **Computer Vision**: `react-webcam` and `@mediapipe/pose` for real-time yoga pose detection, streaming to the backend via WebSockets.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js & npm
- MongoDB running locally or accessible via URI
- Docker & docker-compose (optional, but recommended)

### 1. Environment Setup

You need to create a `.env` file in the `backend/` directory. (Note: No `.env.example` is currently provided in the repo, so you must create it manually).

**Required variables for basic operation:**
```env
MONGODB_URI=mongodb://localhost:27017/deepshiva_tourism
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=168
FRONTEND_URL=http://localhost:5173
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GROQ_API_KEY=your_groq_api_key  # Optional if using local LLM fallback
GROQ_MODEL=moonshotai/kimi-k2-instruct-0905
```

**Variables for specific tools (Optional but required for some API routes/tests):**
```env
LITEAPI_KEY=
CALLENDRIFIC_API_KEY=
KAGGLE_USERNAME=
KAGGLE_KEY=
QDRANT_HOST=
QDRANT_API_KEY=
```

Frontend `.env` (in `frontend/`):
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

### 2. Running Locally

#### Backend
```bash
# Create and activate virtual environment
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`.

### 3. Running with Docker

You can spin up the entire stack using Docker Compose:
```bash
docker compose up --build
```
- Backend exposes port `8000`.
- Frontend exposes port `5173`.

---

## 📚 Data Ingestion for RAG

Before the RAG system can function, you need to ingest the data located in `backend/data/`.

```bash
cd backend
# Make sure your virtual environment is active
python scripts/ingest_all_data.py
# Or for local ChromaDB only:
python scripts/ingest_all_data_local_only.py
```

---

## 🗺️ Project Structure

*   `backend/`
    *   `routers/`: Core API endpoints (`auth.py`, `chat.py`, `yoga.py`, etc.).
    *   `rag/`: RAG logic (`vector_store.py`, `persona_rag.py`).
    *   `tools/`: LLM tool definitions for live data fetching.
    *   `data/`: Knowledge base files (JSON, PDFs) used for RAG.
    *   `scripts/`: Utilities for data ingestion and maintenance.
*   `frontend/`
    *   `src/`: React UI, including 3D components and emergency pages.
    *   `rag_admin_panel/`: Vanilla JS admin interface for managing embeddings.

---

## 📡 Key API Endpoints

- `GET /docs` - Swagger UI documentation.
- `GET /health` - Service health check.
- `POST /api/auth/google` - Google OAuth login.
- `WS /api/yoga/ws` - WebSocket for real-time yoga pose analysis.
- `POST /api/chat/*` - Chat endpoints integrating RAG and multi-personas.
- `POST /api/rag/*` - Admin endpoints for RAG ingestion.

---

## ⚠️ Known Limitations & Current State

- **Missing Files**: The repository lacks an open-source `LICENSE` and a proper `.env.example` file.
- **Local LLM**: The local GGUF fallback requires `llama_cpp` to be correctly compiled for your system's architecture and sufficient RAM.
- **External Dependencies**: Several tools and tests depend heavily on external API keys (Kaggle, LiteAPI, Callendrific). If these are missing, those specific features/tests will fail.
- **Static Assets**: The backend expects `/audio` and `/images` directories in `backend/public/`. Missing files will throw warnings on startup.
