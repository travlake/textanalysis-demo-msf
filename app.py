import json
import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import anthropic
import pdfplumber
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TEXT_LENGTH = 100_000

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url="https://api.anthropic.com",
)

SENTIMENT_PROMPT = (
    "You are a financial analyst. Given the following text, assess whether the "
    "firm has positive, neutral, or negative views about near-run growth.\n\n"
    "You MUST provide:\n"
    "- label: exactly one of \"positive\", \"neutral\", or \"negative\"\n"
    "- score: an integer from 1 to 100 (1 = extremely negative, 50 = neutral, 100 = extremely positive)\n"
    "- justification: a one-sentence explanation\n\n"
    "Respond with ONLY a raw JSON object, no markdown, no code fences, no extra text.\n"
    "Example: {\"label\": \"positive\", \"score\": 72, \"justification\": \"The firm projects strong revenue growth.\"}\n\n"
    "Text:\n"
)

TOPICS_PROMPT = (
    "Identify the main economic topics discussed in the following text. For each "
    "topic, provide a short label, state whether it is a \"major\" or \"minor\" topic in the "
    "text, and explain why it is relevant for investors.\n\n"
    "Respond with ONLY a raw JSON object, no markdown, no code fences, no extra text.\n"
    "Example: {\"topics\": [{\"label\": \"Revenue Growth\", \"significance\": \"major\", \"investor_relevance\": \"Indicates expanding market share.\"}]}\n\n"
    "Text:\n"
)

# Loughran-McDonald financial sentiment word lists (core subset)
LM_POSITIVE = {
    "achieve", "achieved", "achievement", "achievements", "achieves", "achieving",
    "advance", "advanced", "advancement", "advances", "advancing",
    "benefit", "benefited", "beneficial", "benefits", "benefiting",
    "boom", "booming", "boost", "boosted", "boosting", "boosts",
    "confident", "confidence", "creative", "creativity",
    "deliver", "delivered", "delivering", "delivers", "delivery",
    "earn", "earned", "earning", "earnings", "earns",
    "efficient", "efficiency", "enable", "enabled", "enables", "enabling",
    "enhance", "enhanced", "enhancement", "enhances", "enhancing",
    "exceed", "exceeded", "exceeding", "exceeds", "excel", "excelled",
    "expand", "expanded", "expanding", "expansion", "expansions", "expands",
    "favorable", "favourably", "favorably", "gain", "gained", "gaining", "gains",
    "good", "great", "greater", "greatest", "grew", "grow", "growing", "grown", "grows", "growth",
    "ideal", "improve", "improved", "improvement", "improvements", "improves", "improving",
    "increase", "increased", "increases", "increasing", "increasingly",
    "innovative", "innovation", "innovations",
    "leader", "leadership", "leading", "momentum",
    "opportunities", "opportunity", "optimism", "optimistic",
    "outpace", "outpaced", "outpacing", "outperform", "outperformed", "outperforming",
    "positive", "positively", "premium", "profit", "profitability", "profitable", "profits",
    "progress", "progressed", "progressing", "prosper", "prosperity", "prosperous",
    "record", "recover", "recovered", "recovering", "recovery",
    "reward", "rewarded", "rewarding", "rewards",
    "rise", "risen", "rising", "robust",
    "strength", "strengthen", "strengthened", "strengthening", "strengthens", "strong", "stronger", "strongest",
    "succeed", "succeeded", "succeeding", "succeeds", "success", "successes", "successful", "successfully",
    "superior", "surge", "surged", "surging", "surpass", "surpassed",
    "upturn", "upward", "valuable", "win", "winning", "wins", "won",
}

LM_NEGATIVE = {
    "abandon", "abandoned", "abandoning", "abandonment", "abandons",
    "adverse", "adversely", "adversity",
    "challenge", "challenged", "challenges", "challenging",
    "closure", "closures", "collapse", "collapsed", "collapses",
    "concern", "concerned", "concerning", "concerns",
    "contraction", "contractions",
    "cut", "cutback", "cutbacks", "cuts", "cutting",
    "damage", "damaged", "damages", "damaging",
    "danger", "dangerous", "dangers",
    "decline", "declined", "declines", "declining",
    "decrease", "decreased", "decreases", "decreasing",
    "default", "defaulted", "defaulting", "defaults",
    "deficit", "deficits", "delay", "delayed", "delaying", "delays",
    "deteriorate", "deteriorated", "deteriorates", "deteriorating", "deterioration",
    "difficult", "difficulties", "difficulty",
    "disappoint", "disappointed", "disappointing", "disappointment", "disappoints",
    "downturn", "downturns", "downward",
    "drop", "dropped", "dropping", "drops",
    "fail", "failed", "failing", "fails", "failure", "failures",
    "fear", "feared", "fears", "fell",
    "fraud", "frauds", "fraudulent",
    "halt", "halted", "halting", "hardship", "hardships",
    "impair", "impaired", "impairing", "impairment", "impairments",
    "inability", "inadequate", "ineffective", "inefficiency",
    "layoff", "layoffs", "liquidate", "liquidated", "liquidating", "liquidation",
    "litigation", "litigations",
    "lose", "loses", "losing", "loss", "losses", "lost",
    "miss", "missed", "misses", "missing",
    "negative", "negatively",
    "penalty", "penalties", "plummet", "plummeted", "plummeting",
    "poor", "poorly", "problem", "problematic", "problems",
    "recession", "recessionary", "recessions",
    "restructure", "restructured", "restructures", "restructuring",
    "risk", "risked", "riskier", "riskiest", "risking", "risks", "risky",
    "setback", "setbacks", "severe", "severely", "severity",
    "shrink", "shrinkage", "shrinking", "shrinks", "shrunk",
    "slump", "slumped", "slumping", "slumps",
    "struggle", "struggled", "struggles", "struggling",
    "threat", "threaten", "threatened", "threatening", "threatens", "threats",
    "turmoil", "uncertain", "uncertainties", "uncertainty",
    "underperform", "underperformed", "underperforming",
    "unfavorable", "unfavourable",
    "volatile", "volatility", "vulnerability", "vulnerable",
    "warn", "warned", "warning", "warnings", "warns",
    "weak", "weaken", "weakened", "weakening", "weakness", "weaknesses",
    "worsen", "worsened", "worsening", "worsens", "worst", "worse",
    "writedown", "writedowns", "writeoff", "writeoffs",
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "dare", "ought", "used", "it", "its",
    "this", "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
    "he", "him", "his", "she", "her", "they", "them", "their", "what", "which",
    "who", "whom", "where", "when", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "as", "until", "while",
    "about", "between", "through", "during", "before", "after", "above", "below",
    "up", "down", "out", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "also", "into", "if", "any", "per", "s", "t", "re", "ve", "ll",
}


def tokenize(text):
    return re.findall(r"[a-z']+", text.lower())


def bag_of_words(text):
    words = tokenize(text)
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    counts = Counter(filtered)
    top_30 = counts.most_common(30)
    return {"total_words": len(words), "unique_words": len(set(filtered)), "top_words": [{"word": w, "count": c} for w, c in top_30]}


def dictionary_sentiment(text):
    words = tokenize(text)
    pos_hits = [w for w in words if w in LM_POSITIVE]
    neg_hits = [w for w in words if w in LM_NEGATIVE]
    total = len(pos_hits) + len(neg_hits)
    if total == 0:
        score = 50
    else:
        score = round((len(pos_hits) / total) * 100)
    pos_counts = Counter(pos_hits).most_common(10)
    neg_counts = Counter(neg_hits).most_common(10)
    return {
        "positive_count": len(pos_hits),
        "negative_count": len(neg_hits),
        "score": score,
        "top_positive": [{"word": w, "count": c} for w, c in pos_counts],
        "top_negative": [{"word": w, "count": c} for w, c in neg_counts],
    }


def extract_text(file):
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(pages)
    else:
        return file.read().decode("utf-8")


def strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1 :]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    # If still not valid JSON, try to extract the first { ... } block
    if not text.startswith("{"):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
    return text


def call_claude(prompt, text):
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        timeout=60.0,
        messages=[{"role": "user", "content": prompt + text}],
    )
    raw = response.content[0].text
    cleaned = strip_code_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"[DEBUG] Failed to parse Claude response:\n{raw}\n")
        raise


def analyze_sentiment(text):
    return call_claude(SENTIMENT_PROMPT, text)


def analyze_topics(text):
    return call_claude(TOPICS_PROMPT, text)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = file.filename.lower()
    if not (filename.endswith(".txt") or filename.endswith(".pdf")):
        return jsonify({"error": "Only .txt and .pdf files are supported"}), 400

    try:
        text = extract_text(file)
    except Exception as e:
        return jsonify({"error": f"Failed to extract text: {e}"}), 400

    if not text or not text.strip():
        return jsonify({"error": "The uploaded file contains no extractable text"}), 400

    text = text[:MAX_TEXT_LENGTH]

    # Run local analyses immediately
    bow = bag_of_words(text)
    dict_sent = dictionary_sentiment(text)

    # Run LLM analyses in parallel
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            sentiment_future = executor.submit(analyze_sentiment, text)
            topics_future = executor.submit(analyze_topics, text)
            sentiment = sentiment_future.result(timeout=60)
            topics = topics_future.result(timeout=60)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse API response as JSON"}), 502
    except anthropic.APITimeoutError:
        return jsonify({"error": "API request timed out. Please try again."}), 504
    except anthropic.APIError as e:
        return jsonify({"error": f"API error: {e.message}"}), 502
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {e}"}), 500

    # Ensure LLM score is an int in range
    llm_score = sentiment.get("score", 50)
    llm_score = max(1, min(100, int(llm_score)))
    sentiment["score"] = llm_score

    return jsonify({
        "sentiment": sentiment,
        "dictionary_sentiment": dict_sent,
        "bag_of_words": bow,
        "topics": topics,
        "text_preview": text[:500],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
