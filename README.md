# Financial Text Analysis Dashboard

A Flask web app that analyzes uploaded `.txt` and `.pdf` documents using Claude (Sonnet) and traditional NLP techniques. Built as a starting point for students building their own LLM-powered textual analysis tools.

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
- `claude-sonnet-4-20250514` (current — good balance of speed and quality)
- `claude-haiku-4-5-20251001` (faster, cheaper, slightly less capable)
- `claude-opus-4-6` (most capable, slower, more expensive)

### Accept other file types

The `extract_text()` function handles `.txt` and `.pdf`. To add `.docx`, `.csv`, or other formats, add a new branch there and install the relevant parsing library.

## Deploying to PythonAnywhere

1. Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com/)
2. Open a Bash console and clone your repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```
3. Create a virtualenv:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.13 textanalysis
   pip install -r ~/YOUR_REPO/requirements.txt
   ```
4. Create a `.env` file with your API key:
   ```bash
   echo "ANTHROPIC_API_KEY=sk-ant-..." > ~/YOUR_REPO/.env
   ```
5. On the **Web** tab, set:
   - **Source code:** `/home/YOUR_USERNAME/YOUR_REPO`
   - **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/textanalysis`
6. Edit the **WSGI configuration file** (linked on the Web tab):
   ```python
   import sys
   import os

   path = '/home/YOUR_USERNAME/YOUR_REPO'
   if path not in sys.path:
       sys.path.append(path)

   from dotenv import load_dotenv
   load_dotenv(os.path.join(path, '.env'))

   from app import app as application
   ```
7. Hit **Reload** on the Web tab

**Note:** Free PythonAnywhere accounts restrict outbound HTTP to an allowlist. The Anthropic API (`api.anthropic.com`) may require a paid account for unrestricted access.

## For AI Agents

If you're an AI coding agent working on this codebase, read `CLAUDE.md` for project-specific instructions — especially the API configuration requirements around `base_url`.

## Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web framework and routing |
| anthropic | Claude API client |
| pdfplumber | PDF text extraction |
| python-dotenv | Load `.env` variables |
