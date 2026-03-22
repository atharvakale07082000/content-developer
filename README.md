# Content Strategy Agent

A continuously running AI agent built with Google ADK + Gemini 2.5 Flash.

## What it does
- Accepts any input: YouTube URL, blog URL, or free topic
- Analyses content and suggests formats, hooks, audiences, and angles
- Lets you pick suggestions, then drafts LinkedIn posts, email newsletters, and Instagram captions
- UI designed in Google Stitch, pulled via Stitch MCP
- Runs 24/7 on Railway with MongoDB as the job queue

## Stack
- **Agent:** Google ADK (Python)
- **LLM:** Gemini 2.5 Flash
- **Backend API:** FastAPI
- **Queue + Storage:** MongoDB
- **UI:** Google Stitch + Stitch MCP
- **Deployment:** Railway

## Project Structure
```
content-agent/
├── agent/
│   ├── orchestrator.py         # Root LoopAgent — polls queue continuously
│   ├── tools/
│   │   ├── detect_input.py     # Classifies URL / YouTube / topic
│   │   ├── youtube_tool.py     # Fetches YouTube transcript
│   │   ├── scraper_tool.py     # Scrapes blog/article URLs
│   │   └── topic_tool.py       # Expands free-form topics via web search
│   ├── sub_agents/
│   │   ├── analyser.py         # Extracts themes, audience, insights
│   │   ├── suggester.py        # Produces ranked suggestion menu
│   │   └── drafters/
│   │       ├── linkedin.py
│   │       ├── newsletter.py
│   │       └── instagram.py
│   └── prompts/                # System prompts as .txt files
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routes/
│   │   ├── jobs.py             # POST /jobs, GET /jobs/{id}
│   │   └── suggestions.py      # POST /jobs/{id}/pick
│   └── db.py                   # MongoDB client (Motor async)
├── frontend/                   # Stitch MCP pulls HTML here
├── scripts/
│   ├── stitch_setup.sh         # Stitch MCP init helper
│   └── stitch_screens.md       # Screen prompts to paste into Stitch
├── tests/
│   └── test_agent.py
├── .env.example
├── railway.toml
├── Procfile
└── requirements.txt
```

## Quick Start

### 1. Install
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
```

### 2. Set up Stitch UI
```bash
bash scripts/stitch_setup.sh
# Then open stitch.withgoogle.com, create a project,
# paste prompts from scripts/stitch_screens.md into each screen
npx @_davideast/stitch-mcp init
npx @_davideast/stitch-mcp serve -p <your-project-id>
```

### 3. Run locally
```bash
# Terminal 1 — API
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Agent loop
python -m agent.orchestrator
```

### 4. Deploy to Railway
```bash
railway login && railway init && railway up
# Set GEMINI_API_KEY and MONGODB_URI in Railway dashboard
```
