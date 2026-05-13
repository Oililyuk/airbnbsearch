# Lodgic

Open-source AI Airbnb search for people who know the stay they want but cannot express it with normal filters.

Lodgic lets you describe a trip in natural language, then ranks listings by match score, supporting evidence, missing requirements, and booking cautions.

> Authentic farm stay with sheep or horses nearby, quiet, good Wi-Fi, and not a central city flat.

## Why Lodgic Exists

Airbnb filters are good for dates, price, bedrooms, and location. They are weaker at human preferences like:

- quiet enough to write
- real countryside, not a city flat with rustic decor
- animals or farm life nearby
- strong Wi-Fi and a useful desk
- walkable, but not noisy
- cozy fireplace without party-house energy

Lodgic adds an explainable semantic layer on top of listing data. The goal is not to replace Airbnb, but to make shortlisting faster and more trustworthy.

## What It Does

- Ranks Airbnb listings from 0-100 against a natural-language intent
- Shows evidence that supports the match
- Highlights missing or unproven requirements
- Flags cautions before you open the booking page
- Works in mock mode without API keys for local demos
- Supports Apify for Airbnb scraping
- Supports OpenAI-compatible LLMs, including local Ollama models

## Stack

- Frontend: React, Vite, CSS
- Backend: FastAPI
- Listings: Apify Airbnb Scraper
- Reasoning: OpenAI-compatible chat completions

## Quick Start

Backend:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

No API keys are required for the local demo. Lodgic will use mock listings so contributors can see the complete product flow.

## Configuration

Edit `backend/.env`:

```bash
APIFY_TOKEN=your_apify_token_here
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:5173
```

For Ollama or another local OpenAI-compatible server:

```bash
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.2
```

## SEO and GEO Notes

This repository includes:

- `frontend/index.html` with title, meta description, canonical URL, Open Graph tags, Twitter Card tags, and SoftwareApplication JSON-LD
- `llms.txt` for AI crawlers and answer engines
- `robots.txt` and `sitemap.xml` for static hosting
- concise README copy that explains the problem, use case, stack, and local setup

## Project Structure

```text
backend/        FastAPI API, scraper integration, AI scoring
frontend/       React app
demo.html       Standalone bilingual preview
gemini.md       Agent/development guide
llms.txt        AI/answer-engine project summary
```

## Roadmap

- Review-level evidence extraction
- Saved searches and daily alerts
- Map and neighborhood tradeoff summaries
- Hard filters before AI ranking to reduce scraper and token cost
- Shareable shortlists
- Browser extension mode for analyzing already-open Airbnb result pages

## License

Released under the Unlicense.
