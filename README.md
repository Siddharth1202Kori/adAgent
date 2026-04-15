# AdAgent — Multi-Agent CRO Optimizer

A multi-agent AI system that personalizes landing pages based on ad creatives to improve conversion rates. Input an ad (text or image) and a landing page URL — AdAgent analyzes both, identifies strategic mismatches, and generates an optimized version of the page aligned with CRO best practices.

---

## Architecture

AdAgent uses a streamlined 4-phase pipeline:

```
[Phase 1: Analyzer] → [Phase 2: Optimizer] → [Phase 3: Evaluator] → [Phase 4: Renderer]
```

| Phase | Agent | Role |
|-------|-------|------|
| **Analyzer** | `ad_agent.py` | Extracts value proposition, CTA, tone, and audience from the ad (text or image) |
| **Analyzer** | `page_agent.py` | Scrapes and analyzes the landing page structure (hero, features, testimonials) |
| **Analyzer** | `category_gate.py` | Binary check — rejects fundamentally mismatched ad/LP pairs early |
| **Optimizer** | `optimizer.py` | Single chain-of-thought call that infers persona, identifies gaps, and rewrites copy |
| **Evaluator** | `critic_agent.py` | Scores the rewrite on tone alignment, message match, and clarity (threshold: 7/10) |
| **Renderer** | `render_agent.py` | Applies optimized copy to the original HTML while preserving site theme and design |

### RAG Layer

A FAISS-backed retrieval system (`utils/rag.py`) injects CRO frameworks (AIDA, PAS, Message Match, Social Proof) into the Optimizer's context for grounded, principle-driven rewrites.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Mistral AI (Small + Large) via OpenAI-compatible API |
| Backend | FastAPI |
| Frontend | Streamlit |
| Embeddings | Mistral Embed + FAISS |
| Validation | Pydantic v2 |
| Scraping | BeautifulSoup4 + Requests |

---

## Project Structure

```
adAgent/
├── agents/
│   ├── ad_agent.py          # Ad creative analyzer (text + image)
│   ├── page_agent.py        # Landing page analyzer
│   ├── category_gate.py     # Category mismatch detector
│   ├── optimizer.py         # Consolidated CRO optimizer
│   ├── critic_agent.py      # Quality evaluator
│   └── render_agent.py      # HTML renderer (CRO applier)
├── orchestrator/
│   └── pipeline.py          # 4-phase pipeline orchestrator
├── utils/
│   ├── llm.py               # LLM client + retry logic
│   ├── scraper.py           # URL scraping utilities
│   └── rag.py               # FAISS RAG for CRO principles
├── app/
│   ├── main.py              # FastAPI server
│   └── streamlit_app.py     # Streamlit UI
├── requirements.txt
├── run.sh                   # One-command startup script
├── .env.example
└── .gitignore
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/adAgent.git
cd adAgent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Mistral API key:

```
MISTRAL_API_KEY=your_actual_key_here
```

Get a free API key at [console.mistral.ai](https://console.mistral.ai/)

### 5. Run the application

```bash
bash run.sh
```

This starts:
- **FastAPI backend** on `http://127.0.0.1:8000`
- **Streamlit frontend** on `http://localhost:8501`

---

## Usage

1. Open `http://localhost:8501` in your browser
2. In the sidebar, choose **Text** or **Image Upload** for the ad input
3. Paste the **Landing Page URL**
4. Click **Optimize**
5. View results:
   - **Original vs Optimized** text comparison
   - **Category Gate** pass/fail status
   - **Critic Scores** (Tone, Message Match, Clarity)
   - **Visual Preview** — original HTML alongside the CRO-optimized version

---

## API Endpoint

```
POST /personalize
```

**Request Body:**

```json
{
  "ad_text": "Get 50% off premium sneakers!",
  "lp_url": "https://example.com/sneakers",
  "ad_image_base64": null
}
```

**Response:** JSON containing ad analysis, LP analysis, category gate result, optimizer output, critic scores, and rendered HTML.

---

## Rate Limit Handling

All LLM calls use exponential backoff (`2^attempt` scaling) with 5 retries. Sequential `time.sleep(2)` pauses between pipeline phases prevent RPM exhaustion on Mistral's free tier.

---

## License

MIT
