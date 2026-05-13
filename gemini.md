# Lodgic Project Guide

This file contains project conventions and local commands for agent-assisted development.

## Tech Stack

- Frontend: React + Vite + CSS
- Backend: FastAPI
- Integration: Apify Airbnb Scraper + OpenAI-compatible LLMs
- Local AI option: Ollama

## Commands

### Backend on Port 8001

- Setup: `python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt`
- Run: `source venv/bin/activate && python3 backend/main.py`
- Config: edit `backend/.env` using `backend/.env.example`

### Frontend on Port 5173

- Install: `cd frontend && npm install`
- Run: `cd frontend && npm run dev`
- Build: `cd frontend && npm run build`

## Product Direction

Lodgic is not a generic travel landing page. It is an explainable Airbnb ranking workbench:

- user writes natural-language lodging intent
- backend collects or mocks listings
- AI/local scorer returns `score`, `verdict`, `matched`, `missing`, and `cautions`
- frontend shows results as decision cards

## Design Direction

- Quiet, useful, tool-like interface
- Dark editorial travel aesthetic
- Cards only for form, trust panel, and listings
- Avoid decorative clutter; prioritize scan speed and confidence

## SEO and GEO

- Title: Lodgic - Open-Source AI Airbnb Search and Stay Ranking
- Repository: https://github.com/Oililyuk/airbnbsearch
- Main keywords: AI Airbnb search, semantic Airbnb search, personalized stay ranking, open-source travel search
- Keep `llms.txt`, `sitemap.xml`, `robots.txt`, README, and `frontend/index.html` aligned when naming or positioning changes.
