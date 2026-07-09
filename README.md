# HeadHunter Agent — Public Version

> **AI-Powered Job Application Agent for the German IT Market 2026**
>
> Reads a job posting → Analyzes requirements → Calculates ATS match score → Generates tailored CV + Cover Letter + PDF

---

## What This Does

This agent automates the German job application workflow in **5 steps**:

| Step | Action | Output |
|---|---|---|
| 1. ANALYSE | Parses job posting (Stellenanzeige) | Structured JSON (skills, ATS, salary) |
| 2. MATCH | Calculates ATS compatibility (0–100) | Match report with gaps & strengths |
| 3. LEBENSLAUF | Adapts your master CV to the vacancy | ATS-optimized Markdown CV |
| 4. ANSCHREIBEN | Generates cover letter (DIN 5008) | 1-page, 4-paragraph cover letter |
| 5. OUTPUT | Saves all files + builds PDF | Complete application package |

---

## Quick Start

### Prerequisites

- **Python 3.10+** — [python.org](https://python.org)
- **pip** — `pip install httpx`
- **PDF engine** (optional) — `winget install wkhtmltopdf pandoc` (Windows) or `apt install wkhtmltopdf pandoc` (Linux)

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/headhunter-public.git
cd headhunter-public
pip install httpx
```

### 2. Fill in Your Profile

**⚠️ CRITICAL — Replace all placeholder data with your own!**

Edit these two files:
- `DATABASE/00_CANDIDATE_PROFILE/kandidat_profil.md` — Your personal data, skills, experience
- `DATABASE/00_CANDIDATE_PROFILE/lebenslauf_master.md` — Your master CV (ATS-clean Markdown)

All fields marked with `[...]` must be replaced with your real data.

### 3. Get an API Key (FREE)

**Option A — Mistral AI (recommended, best German):**
1. Register at [console.mistral.ai](https://console.mistral.ai)
2. Create API key
3. Set environment variable: `export MISTRAL_API_KEY=your_key_here`

**Option B — OpenRouter (200 free requests/day):**
1. Register at [openrouter.ai/keys](https://openrouter.ai/keys)
2. Create API key
3. Set: `export OPENROUTER_API_KEY=your_key_here`

### 4. Run a Test

```bash
# Dry-run test (no LLM, instant):
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode dry-run

# Real run with Mistral:
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode mistral

# With OpenRouter:
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode openrouter
```

### 5. Find Results

```
OUTPUT/Bewerbungen/[DATE]_[COMPANY]_[ROLE]/
  ├── lebenslauf_[company].md     ← Adapted CV
  ├── lebenslauf_[company].pdf    ← PDF
  ├── anschreiben_[company].md    ← Cover letter
  └── ANALYSE_REPORT.md           ← ATS score + analysis
```

---

## LLM Backends

| Mode | Backend | Cost | Command |
|---|---|---|---|
| `mistral` | Mistral Large Latest | Free tier | `--mode mistral` |
| `openrouter` | OpenRouter (Gemma/Llama/GPT) | Free (200/day) | `--mode openrouter` |
| `ollama` | Local Ollama | Free, offline | `--mode ollama` |
| `api` | OpenAI | Paid | `--mode api` |
| `dry-run` | Regex only | Free, instant | `--mode dry-run` |

### Local Ollama Setup

```bash
# Install Ollama:
winget install Ollama.Ollama    # Windows
# or: curl -fsSL https://ollama.com/install.sh | sh  # Linux/macOS

# Pull the public HeadHunter model:
ollama pull lelegioner/headhunter-public

# Run agent with local model:
python DATABASE/04_AUTOMATION/agent.py --vacancy job.txt --mode ollama --model lelegioner/headhunter-public
```

---

## Test Vacancy Walkthrough

The project includes a test vacancy: `DATABASE/04_AUTOMATION/test_vacancy.txt` — "IT System Engineer (m/w/d) – Linux & Windows" at Servator Consulting GmbH.

**Step-by-step verification:**

```bash
# 1. Verify structure (dry-run):
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode dry-run

# 2. Real run with Mistral:
python DATABASE/04_AUTOMATION/agent.py --vacancy DATABASE/04_AUTOMATION/test_vacancy.txt --mode mistral

# 3. Check output:
ls -la OUTPUT/Bewerbungen/

# 4. Initialize tracking database (optional):
python DATABASE/04_AUTOMATION/setup_ats_db.py

# 5. Check available backends:
python DATABASE/04_AUTOMATION/check_backends.py
```

---

## Customization for Other Profiles

To use this for a different candidate/role:

1. Edit `kandidat_profil.md` — replace ALL `[...]` placeholders with real data
2. Edit `lebenslauf_master.md` — replace the CV template with your own
3. Update `agent.py` — adjust transfer arguments in `build_anschreiben_prompt()` (around line 520)
4. Test with `--mode dry-run` before running with a real LLM

**Example for Java Developer:**
```yaml
# In kandidat_profil.md:
primary_targets:
  - "Junior Java Developer"
  - "Java Backend Developer"
hard_skills:
  - "Java 21, Spring Boot 3, REST API, PostgreSQL, Docker, Git"
```

---

## Project Structure

```
headhunter-public/
├── README.md                          ← You are here
├── .env.example                       ← API key template
├── AGENTS.md                          ← Agent workflow rules (template)
├── BENUTZERHANDBUCH.md                ← Full user manual (Russian)
├── CLOUD_PUBLISH_GUIDE.md             ← Cloud deployment guide
├── OLLAMA_MODEL_CARD.md               ← Public Ollama model description
├── Modelfile.public                   ← Clean Modelfile for Ollama Hub
├── opencode.jsonc                     ← Opencode CLI config
├── DATABASE/
│   ├── 00_CANDIDATE_PROFILE/          ← ⚠️ FILL WITH YOUR DATA
│   │   ├── kandidat_profil.md         ←    Your profile (YAML + MD)
│   │   └── lebenslauf_master.md       ←    Your master CV
│   ├── 01_STANDARDS/                  ← EU AI Act, DIN, ISO standards
│   ├── 02_ATS_SYSTEMS/                ← ATS map for Germany
│   ├── 03_TEMPLATES/                  ← CV/cover letter templates
│   ├── 04_AUTOMATION/                 ← ★ Python scripts
│   │   ├── agent.py                   ←   Main pipeline
│   │   ├── setup_ats_db.py            ←   DB initializer
│   │   ├── cv_optimizer_prompt.py     ←   CV optimizer
│   │   ├── mcp_server.py              ←   Opencode MCP server
│   │   ├── check_backends.py          ←   Backend health check
│   │   └── test_vacancy.txt           ←   Sample job posting
│   ├── 05_DATABASE/                   ← SQLite schema
│   ├── 06_SKILLS/                     ← DE IT skills map 2026
│   └── 07_TRAINING_DOCS/              ← Training materials
├── .opencode/
│   └── agent/headhunter.md            ← Opencode agent definition
└── OUTPUT/Bewerbungen/                ← Generated applications
```

---

## Compliance

- **EU AI Act (Annex III):** This agent is a *drafting assistant*, not a decision-maker. Always review outputs before submitting.
- **Human-in-the-Loop:** Required for all AI-generated applications in Germany.
- **GDPR:** Store API keys in `.env` (never commit to git). Use `--mode ollama` for maximum privacy.

---

## License

- Agent code & workflow: **MIT**
- Base Ollama model: **Meta Llama 3.2 Community License**
- Use for job applications is permitted under both licenses.

---

## Links

- 📦 Public Ollama model: [ollama.com/lelegioner/headhunter-public](https://ollama.com/lelegioner/headhunter-public)
- 📖 Full docs: `BENUTZERHANDBUCH.md` (Russian) | `AGENTS.md` (German workflow)
- 🔑 Get API keys: [console.mistral.ai](https://console.mistral.ai) | [openrouter.ai/keys](https://openrouter.ai/keys)
