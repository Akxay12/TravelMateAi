# TravelMate AI 2.0

A clean-room rebuild of TravelMate as a simple, modular, production-ready travel planning application.

## Architecture

```
3-Step Flow:
1. Trip Form  →  2. Select Real Attractions  →  3. AI-Organized Itinerary

Backend: FastAPI + SQLite + Overpass API + Google Gemini
Frontend: React + TypeScript + Vite + Tailwind CSS
```

## Quick Start

### 1. Configure API Key

Edit `backend/.env` and set your Gemini API key:

```
GEMINI_API_KEY=your_key_here
```

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on: http://localhost:8000
API docs: http://localhost:8000/docs

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| POST | /api/trips | Save trip |
| POST | /api/attractions/search | Fetch real OSM attractions |
| POST | /api/itinerary/generate | Generate AI itinerary |

## Design Principles

- **No multi-agent system** — 3 simple services with one job each
- **No cache** — direct API calls only
- **No fallback engine** — if OSM fails, it fails clearly
- **No fake attractions** — only real OpenStreetMap data
- **No AI at step 2** — Gemini is called only when user clicks "Generate AI Plan"
