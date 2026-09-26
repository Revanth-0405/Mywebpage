"""
Revanth Balaji — Portfolio Backend
Flask application serving the portfolio and handling API endpoints.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests
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
# API: Chatbot
# ─────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Simple keyword-based chatbot endpoint.
    In production, swap the logic here for an LLM API call.
    """
    data = request.json
    question = data.get("question", "").lower().strip()
    kb = PORTFOLIO_KB

    if any(w in question for w in ["who", "about", "introduce", "revanth", "tell me"]):
        reply = (
            f"{kb['bio']}\n\n"
            f"He's currently completing his {kb['education']['degree']} "
            f"({kb['education']['duration']}) and seeking opportunities in backend and AI engineering."
        )

    elif any(w in question for w in ["skill", "tech", "know", "language", "stack"]):
        s = kb["skills"]
        reply = (
            f"Revanth's tech stack:\n"
            f"• Backend: {', '.join(s['backend'])}\n"
            f"• Database: {', '.join(s['database'])}\n"
            f"• Cloud: {', '.join(s['cloud'])}\n"
            f"• AI/ML: {', '.join(s['ai'])}\n"
            f"• Tools: {', '.join(s['tools'])}"
        )

    elif any(w in question for w in ["project", "built", "build", "made", "created"]):
        projects = "\n\n".join(
            f"• {p['name']}: {p['description']} [{', '.join(p['tech'])}]"
            for p in kb["projects"]
        )
        reply = f"He has built {len(kb['projects'])} featured projects:\n\n{projects}"

    elif any(w in question for w in ["intern", "work", "experience", "job", "company"]):
        exp = kb["experience"][0]
        bullets = "\n".join(f"• {h}" for h in exp["highlights"])
        reply = (
            f"{exp['role']} at {exp['company']} ({exp['duration']}):\n\n{bullets}"
        )

    elif any(w in question for w in ["cert", "certif", "credential"]):
        certs = "\n".join(f"• {c}" for c in kb["certifications"])
        reply = f"Revanth holds {len(kb['certifications'])} certifications:\n\n{certs}"

    elif any(w in question for w in ["contact", "email", "reach", "linkedin", "github", "hire"]):
        c = kb["contact"]
        reply = (
            f"You can reach Revanth at:\n"
            f"📧 {c['email']}\n"
            f"💼 {c['linkedin']}\n"
            f"💻 {c['github']}\n"
            f"📍 {c['location']}"
        )

    elif any(w in question for w in ["ai", "llm", "rag", "ml", "nlp", "chatbot"]):
        reply = (
            "Revanth's AI work includes:\n"
            "• Educational Chatbot using Rasa NLU & NLP\n"
            "• NL2SQL research with Llama 3.1 & RAG\n"
            "• AI SDR Lead Qualification using LLM pipelines\n\n"
            f"AI skills: {', '.join(kb['skills']['ai'])}"
        )

    else:
        reply = (
            "I can help you learn about Revanth! Try asking about:\n"
            "• Skills & tech stack\n"
            "• Projects he's built\n"
            "• Internship experience\n"
            "• Certifications\n"
            "• Contact information"
        )

    return jsonify({"success": True, "reply": reply})


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
