# Revanth Balaji — Portfolio Website

A modern, premium Software Engineer portfolio with dark theme, glassmorphism UI, smooth animations, and an integrated AI chatbot.

---

## 📁 Project Structure

```
revanth-portfolio/
├── index.html              # Main portfolio (all-in-one: HTML + CSS + JS)
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── Procfile                # For Heroku / Railway / Render
├── data/
│   ├── portfolio_kb.json   # AI chatbot knowledge base
│   └── messages.json       # Contact form submissions (auto-created)
└── static/
    └── resume.pdf          # Your resume (add this!)
```

---

## 🚀 Local Development

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/portfolio.git
cd portfolio
pip install -r requirements.txt
```

### 2. Add Your Resume

Place your resume PDF at `static/resume.pdf`.

### 3. Add Your Photo

Replace the emoji placeholder in `index.html` (search for `hero-img-circle`) with:

```html
<img src="static/profile.jpg" class="hero-img-circle" alt="Revanth Balaji">
```

### 4. Update Personal Info

Edit `data/portfolio_kb.json` with your actual info, and update `index.html` social links.

### 5. Run Locally

```bash
python app.py
```

Visit: `http://localhost:5000`

---

## 🌐 Deployment

### Option A — GitHub Pages (static only)
Push to GitHub, enable Pages on `main` branch. The `index.html` is fully self-contained.

### Option B — Vercel (recommended for full-stack)
```bash
npm i -g vercel
vercel
```

### Option C — Render
1. Push to GitHub
2. New Web Service on render.com
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app`

### Option D — Railway
1. Push to GitHub
2. Connect repo on railway.app
3. Deploys automatically using `Procfile`

---

## 📬 Contact Form Email (Optional)

Set environment variables for SMTP:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your_app_password
CONTACT_TO=your@gmail.com
```

---

## ✨ Customization Checklist

- [ ] Replace emoji with your photo in `index.html`
- [ ] Add `static/resume.pdf`
- [ ] Update GitHub / LinkedIn / Email links
- [ ] Edit `data/portfolio_kb.json` with real details
- [ ] Update project GitHub & Demo links
- [ ] Replace placeholder company names in timeline
- [ ] Set SMTP env vars for live email

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | HTML5, CSS3 (custom), Vanilla JS |
| Backend | Python 3.11+, Flask 3.0 |
| Fonts | Space Grotesk, JetBrains Mono |
| Icons | Font Awesome 6 |
| Deployment | GitHub Pages / Vercel / Render / Railway |

---

Built with ❤️ by Revanth Balaji
