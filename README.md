# Financial Text Analysis Dashboard

A Flask web app that analyzes uploaded `.txt` and `.pdf` documents using Claude (Sonnet) and traditional NLP techniques. Developed for **FIN 284T: AI and Portfolio Management** (MSF program, McCombs School of Business) as a starting point for students building their own LLM-powered textual analysis tools.

**Live demo:** [travlake.pythonanywhere.com](https://travlake.pythonanywhere.com)

## What It Does

Upload a financial document and get back:

- **LLM Sentiment Score (1-100)** — Claude reads the full text and returns a sentiment label, numeric score, and justification, displayed as an animated gauge
- **Dictionary Sentiment** — Word-level sentiment using the [Loughran-McDonald](https://sraf.nd.edu/loughranmcdonald-master-dictionary/) financial word lists (no LLM needed), with a positive/negative breakdown bar
- **Bag of Words** — Word frequency analysis with total/unique counts and a weighted word cloud of top terms
- **Topic Modeling** — Claude identifies major and minor economic topics and explains their investor relevance

## Project Structure

```
├── app.py                  # Flask backend — routes, Claude API calls, local NLP
├── templates/
│   └── index.html          # Single-page frontend — upload UI, gauge, cards (inline CSS/JS)
├── prompts.txt             # Reference prompts (sentiment + topics)
├── requirements.txt        # Python dependencies
├── .env                    # Your API key (not committed — see setup below)
└── CLAUDE.md               # Instructions for AI coding agents working on this repo
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/travlake/textanalysis-demo-msf.git
cd textanalysis-demo-msf
pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

Get a key at [console.anthropic.com](https://console.anthropic.com/).

### 3. Run locally

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) and upload a `.txt` or `.pdf` file.

## How It Works

### Architecture

```
Browser (index.html)
  │  POST /analyze (multipart file upload)
  ▼
Flask (app.py)
  ├─ Extract text (pdfplumber for PDFs, decode for .txt)
  ├─ Local analysis (instant, no API cost):
  │    ├─ Bag of words → word frequencies
  │    └─ Dictionary sentiment → Loughran-McDonald word matching
  └─ LLM analysis (parallel API calls via ThreadPoolExecutor):
       ├─ Sentiment → label + score 1-100 + justification
       └─ Topics → list of topics with significance + relevance
  │
  ▼  JSON response
Browser renders gauge, cards, word cloud
```

### Key Design Decisions

- **Parallel API calls** — Sentiment and topic calls run concurrently in a `ThreadPoolExecutor`, cutting wait time roughly in half
- **Structured JSON output** — Prompts include explicit JSON schemas and examples so Claude returns parseable responses. A fallback strips markdown fences and regex-extracts JSON if needed
- **No database** — Everything is stateless. Text is extracted in memory, sent to the API, and discarded. This keeps the app simple and avoids storing sensitive documents
- **Hybrid analysis** — Combining LLM analysis with dictionary-based methods lets you compare AI judgment against a transparent, reproducible baseline

## Customizing for Your Own Project

This repo is designed to be forked and adapted. Here are the most common modifications:

### Change the analysis domain

The prompts in `app.py` (`SENTIMENT_PROMPT`, `TOPICS_PROMPT`) are written for financial text. To analyze a different domain:

1. Rewrite the prompt strings to describe your domain (e.g., legal documents, medical notes, product reviews)
2. Update the dictionary word lists (`LM_POSITIVE`, `LM_NEGATIVE`) — the current lists are finance-specific. For general sentiment, consider using a general-purpose lexicon
3. Update the JSON schema in the prompt to request whatever fields you need

### Add a new analysis type

To add a new LLM-powered analysis (e.g., named entity extraction, risk scoring, summarization):

1. Add a new prompt string in `app.py`
2. Create a function like `analyze_entities(text)` that calls `call_claude(YOUR_PROMPT, text)`
3. Add it to the `ThreadPoolExecutor` block in the `/analyze` route
4. Add a new card in `index.html` to display the results

### Change the model

Edit the `MODEL` variable in `app.py`. Options include:
- `claude-sonnet-4-6` (current — good balance of speed and quality)
- `claude-haiku-4-5-20251001` (faster, cheaper, slightly less capable)
- `claude-opus-4-6` (most capable, slower, more expensive)

### Swap in a different LLM provider

The app uses the Anthropic SDK, but the pattern is easy to adapt to any LLM API. The `call_claude()` function is the only place the API is called — replace it with a call to OpenAI, Google Gemini, Mistral, or any provider that accepts a text prompt and returns a text response. The prompts themselves are plain text and not Anthropic-specific, so they transfer directly.

### Accept other file types

The `extract_text()` function handles `.txt` and `.pdf`. To add `.docx`, `.csv`, or other formats, add a new branch there and install the relevant parsing library.

## Deployment

The app is a standard Flask application with no database, no background workers, and no platform-specific code. It runs anywhere Python runs. Some low-friction options:

- **[PythonAnywhere](https://www.pythonanywhere.com/)** — Browser-based setup, no CLI needed. Clone your repo, create a virtualenv, point the WSGI config at your app, and set your API key as an environment variable. Free tier available (may restrict outbound API calls).
- **[Render](https://render.com/)** — Connect your GitHub repo and deploy automatically on push. Free tier available.
- **[Railway](https://railway.app/)** — Similar Git-based deploy. Detects Flask apps automatically.
- **[Heroku](https://www.heroku.com/)** — Add a `Procfile` with `web: gunicorn app:app` and deploy via Git.
- **Any VPS** (DigitalOcean, AWS EC2, etc.) — `pip install`, set your `.env`, and run behind gunicorn/nginx.

For all platforms, you'll need to set the `ANTHROPIC_API_KEY` environment variable (or deploy a `.env` file) and ensure the host allows outbound HTTPS to `api.anthropic.com`.

## For AI Agents

If you're an AI coding agent working on this codebase, read `CLAUDE.md` for project-specific instructions — especially the API configuration requirements around `base_url`.

## Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework and routing |
| anthropic | Claude API client |
| pdfplumber | PDF text extraction |
| python-dotenv | Load `.env` variables |
