"""
Revanth Balaji — Portfolio Backend
Flask application serving the portfolio and handling API endpoints.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests
import time
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder=".")

# Allow requests from your GitHub Pages site (and localhost while testing).
# Replace the github.io URL with your actual Pages URL.
CORS(app, resources={r"/api/*": {"origins": [
    "https://revanth-0405.github.io",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]}})

# ─────────────────────────────────────────────
# Portfolio Knowledge Base (used by chatbot)
# ─────────────────────────────────────────────
KB_PATH = os.path.join(os.path.dirname(__file__), "portfolio_kb.json")
with open(KB_PATH, "r") as f:
    PORTFOLIO_KB = json.load(f)


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main portfolio page."""
    return send_from_directory(".", "index.html")


@app.route("/resume.pdf")
def resume():
    """Serve the resume PDF."""
    return send_from_directory("static", "resume.pdf")


# ─────────────────────────────────────────────
# API: Contact Form
# ─────────────────────────────────────────────

@app.route("/api/contact", methods=["POST"])
def contact():
    """Receive and process contact form submissions."""
    data = request.json
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    subject = data.get("subject", "").strip()
    message = data.get("message", "").strip()

    if not all([name, email, subject, message]):
        return jsonify({"success": False, "error": "All fields are required."}), 400

    # Log to file (replace with email sending in production)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
    }

    log_path = os.path.join(os.path.dirname(__file__), "data", "messages.json")
    messages = []
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            messages = json.load(f)
    messages.append(log_entry)
    with open(log_path, "w") as f:
        json.dump(messages, f, indent=2)

    # Send an email notification (configured via env vars on Render)
    email_sent = _send_email(name, email, subject, message)

    return jsonify({"success": True, "message": "Message received!", "email_sent": email_sent}), 200


# ─────────────────────────────────────────────
# API: Chatbot (Gemini Flash-powered, grounded in portfolio_kb.json)
# ─────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = (
    "You are the AI assistant embedded on Revanth Balaji's personal portfolio website. "
    "You answer visitors' questions about Revanth using ONLY the facts in the JSON data "
    "below. Speak about him in the third person, in a friendly, concise, professional tone, "
    "as if you simply know him — never mention that you're reading from a 'profile', 'data', "
    "'JSON', 'the information provided', or similar. Don't preface answers with phrases like "
    "'Based on his profile' or 'According to the data' — just answer directly, the way a "
    "knowledgeable colleague would. "
    "Use short paragraphs or bullet points where that reads better. "
    "If a question asks something not covered by this data (e.g. his personal opinions, "
    "unrelated general knowledge, or anything not listed here), say you don't have that "
    "information and suggest they reach out to Revanth directly via the contact info below. "
    "Never invent facts, dates, employers, or skills that aren't in the data.\n\n"
    f"PORTFOLIO DATA (JSON):\n{json.dumps(PORTFOLIO_KB, indent=2)}"
)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")  # override via env var if needed; check https://ai.google.dev/gemini-api/docs/rate-limits for current free-tier models
GEMINI_FALLBACK_MODEL = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.1-flash-lite")  # tried if the primary model is overloaded (503)


def _call_gemini(model, api_key, contents):
    """Single call to Gemini's generateContent endpoint. Returns the requests.Response."""
    return requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": contents,
            "systemInstruction": {"parts": [{"text": CHAT_SYSTEM_PROMPT}]},
            "generationConfig": {"maxOutputTokens": 500},
        },
        timeout=20,
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    """LLM-powered chatbot endpoint (Google Gemini Flash, free tier). Answers are grounded in PORTFOLIO_KB."""
    data = request.json or {}
    question = (data.get("question") or "").strip()
    history = data.get("history") or []  # optional: [{"role": "user"/"assistant", "content": "..."}]

    if not question:
        return jsonify({"success": False, "error": "Question is required."}), 400

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return jsonify({
            "success": True,
            "reply": "The AI assistant isn't fully configured yet — please reach out to Revanth directly using the contact section above!"
        })

    # Keep only the last few turns to bound context size
    trimmed_history = history[-8:]

    # Gemini uses "model" instead of "assistant" for the bot's turns
    contents = [
        {"role": ("model" if turn.get("role") == "assistant" else "user"),
         "parts": [{"text": turn.get("content", "")}]}
        for turn in trimmed_history
    ]
    contents.append({"role": "user", "parts": [{"text": question}]})

    # Try the primary model with a couple of quick retries on 503 (overload),
    # then fall back to a lighter model that's usually less contended.
    attempts = [
        (GEMINI_MODEL, 0),
        (GEMINI_MODEL, 1.5),
        (GEMINI_FALLBACK_MODEL, 0),
    ]

    last_error = None
    for model, delay in attempts:
        if delay:
            time.sleep(delay)
        try:
            res = _call_gemini(model, api_key, contents)
        except requests.RequestException as e:
            print(f"Chatbot request failed ({model}): {e}")
            last_error = str(e)
            continue

        if res.status_code == 503:
            print(f"Gemini API 503 (overloaded) on {model} — retrying/falling back...")
            last_error = "503 overloaded"
            continue

        if res.status_code >= 400:
            print(f"Gemini API error {res.status_code} ({model}): {res.text}")
            last_error = f"{res.status_code}: {res.text}"
            continue

        payload = res.json()
        candidates = payload.get("candidates") or []
        reply_text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            reply_text = "".join(p.get("text", "") for p in parts).strip()

        if not reply_text:
            reply_text = "Sorry, I couldn't come up with an answer to that — try rephrasing, or ask about Revanth's skills, projects, or experience."

        return jsonify({"success": True, "reply": reply_text})

    # All attempts failed
    print(f"All Gemini attempts failed. Last error: {last_error}")
    return jsonify({
        "success": True,
        "reply": "Sorry, I'm having trouble answering right now — please try again in a moment, or use the contact form above."
    })



# ─────────────────────────────────────────────
# Helper: Send email via Resend (HTTP API — not blocked on Render free tier)
# ─────────────────────────────────────────────

def _send_email(name, sender_email, subject, message):
    """
    Send a contact-form notification email via Resend's HTTP API.

    Render's free tier blocks outbound SMTP ports (25/465/587), so we send
    over plain HTTPS instead. Set these env vars on Render:
      RESEND_API_KEY  - your Resend API key
      CONTACT_FROM    - verified sender, e.g. "Portfolio <onboarding@resend.dev>"
                         (or a sender on your own verified domain)
      CONTACT_TO      - the inbox that should receive messages (your email)
    """
    api_key   = os.environ.get("RESEND_API_KEY", "")
    from_addr = os.environ.get("CONTACT_FROM", "Portfolio <onboarding@resend.dev>")
    to_addr   = os.environ.get("CONTACT_TO", "")

    if not api_key or not to_addr:
        print("Resend not configured (RESEND_API_KEY or CONTACT_TO missing) — skipping email send.")
        return False

    html_body = (
        f"<p><strong>From:</strong> {name} &lt;{sender_email}&gt;</p>"
        f"<p><strong>Subject:</strong> {subject}</p>"
        f"<p>{message}</p>"
    )

    try:
        res = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": from_addr,
                "to": [to_addr],
                "reply_to": sender_email,
                "subject": f"[Portfolio] {subject}",
                "html": html_body,
            },
            timeout=10,
        )
        if res.status_code >= 400:
            print(f"Resend error {res.status_code}: {res.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"Email send failed: {e}")
        return False


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
