"""
Revanth Balaji — Portfolio Backend
Flask application serving the portfolio and handling API endpoints.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder=".")

# ─────────────────────────────────────────────
# Portfolio Knowledge Base (used by chatbot)
# ─────────────────────────────────────────────
with open("data/portfolio_kb.json", "r") as f:
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

    log_path = "data/messages.json"
    messages = []
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            messages = json.load(f)
    messages.append(log_entry)
    with open(log_path, "w") as f:
        json.dump(messages, f, indent=2)

    # ── Optional: send email via SMTP ──────────
    # _send_email(name, email, subject, message)

    return jsonify({"success": True, "message": "Message received!"}), 200


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
# Helper: Send email (configure SMTP in prod)
# ─────────────────────────────────────────────

def _send_email(name, sender_email, subject, message):
    """Send contact form email. Set env vars before use."""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    to_email  = os.environ.get("CONTACT_TO", smtp_user)

    if not smtp_user:
        return  # Skip if not configured

    body = f"From: {name} <{sender_email}>\n\n{message}"
    msg = MIMEText(body)
    msg["Subject"] = f"[Portfolio] {subject}"
    msg["From"] = smtp_user
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        print(f"Email send failed: {e}")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
