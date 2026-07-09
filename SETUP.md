# 🛠️ Cross-Platform Setup Guide
## HeadHunter Agent — German IT Job Application Automation

---

## 1. Prerequisites

| Requirement | Version | Windows | Linux (Debian/Ubuntu) | macOS |
|---|---|---|---|---|
| Python | ≥ 3.10 | [python.org](https://python.org) | `sudo apt install python3 python3-pip` | `brew install python3` |
| git | any | `winget install Git.Git` | `sudo apt install git` | `brew install git` |

---

## 2. Python Dependencies

```bash
# All platforms:
pip install -r requirements.txt

# On Linux with externally-managed Python:
pip install -r requirements.txt --break-system-packages

# Or use a virtual environment:
python3 -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate           # Windows PowerShell
pip install -r requirements.txt
```

---

## 3. PDF Engine (at least one)

The agent tries engines in this order: **pandoc+wkhtmltopdf** → **wkhtmltopdf** → **weasyprint**.

| Engine | Windows | Linux | macOS |
|---|---|---|---|
| **weasyprint** (Python) | `pip install weasyprint` | `pip install weasyprint` | `pip install weasyprint` |
| **wkhtmltopdf** (system) | `winget install wkhtmltopdf` | `sudo apt install wkhtmltopdf` | `brew install wkhtmltopdf` |
| **pandoc** (system) | `winget install JohnMacFarlane.Pandoc` | `sudo apt install pandoc` | `brew install pandoc` |

**Recommendation:**
- **Linux:** `weasyprint` is easiest (pure Python, already in `requirements.txt`)
- **Windows:** `winget install wkhtmltopdf` — clean install, no dependencies
- **macOS:** `brew install wkhtmltopdf`

---

## 4. LLM Backend (API Key)

| Backend | URL | Cost | Setup |
|---|---|---|---|
| **Mistral** (recommended) | [console.mistral.ai](https://console.mistral.ai) | Free tier | `export MISTRAL_API_KEY=your_key` |
| **OpenRouter** | [openrouter.ai/keys](https://openrouter.ai/keys) | 200 req/day free | `export OPENROUTER_API_KEY=your_key` |
| **Ollama** (local) | [ollama.com](https://ollama.com) | Free, offline | `ollama pull lelegioner/headhunter-public` |

Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

---

## 5. Quick Verification

```bash
# 1. Dry-run (no LLM, instant):
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode dry-run

# 2. Full test with Mistral:
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode mistral

# 3. Check backends:
python DATABASE/04_AUTOMATION/check_backends.py

# 4. Initialize tracking DB:
python DATABASE/04_AUTOMATION/setup_ats_db.py
```

---

## 6. Expected Output

```
OUTPUT/Bewerbungen/[DATE]_[COMPANY]_[ROLE]/
├── lebenslauf_[company].md      ← Adapted CV
├── lebenslauf_[company].pdf     ← PDF (if engine installed)
├── anschreiben_[company].md     ← Cover letter (DIN 5008)
└── ANALYSE_REPORT.md            ← ATS score + match report
```

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| `httpx not installed` | `pip install httpx` |
| PDF not generated | Install one PDF engine (see §3) |
| `MISTRAL_API_KEY not set` | `export MISTRAL_API_KEY=your_key` or use `--apikey` |
| `DB nicht gefunden` | Auto-initializes on first run, or run `setup_ats_db.py` |
| HTML files left in OUTPUT | Fixed in v2.1 — temp files auto-clean |
| `Permission denied` (SSH push) | `chmod 600 ~/.ssh/id_ed25519` |

---

> **Full docs:** `README.md` (English) | `BENUTZERHANDBUCH.md` (Русский) | `AGENTS.md` (Workflow)
