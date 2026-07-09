# HeadHunter Agent — German IT Job Application Assistant

> **Specialized LLM for automated German IT job applications, ATS optimization,  
> and cover letter generation for the 2026 German labor market.**

📦 **Base model:** `llama3.2:3b-instruct-q4_K_M`  
🖥️ **Optimized for:** CPU-only inference (no GPU required)  
🇩🇪 **Primary language:** German (documents) + Russian (analysis reports)  
🔗 **Project:** [HeadHunter Public](https://github.com/headhunter-public)

---

## What This Model Does

HeadHunter Agent is a role-conditioned LLM that automates the German job application process in **5 structured steps**:

| Step | Action | Output |
|---|---|---|
| 1. ANALYSE | Parses a job posting (Stellenanzeige) | Structured JSON with skills, ATS system, salary |
| 2. MATCH | Calculates ATS compatibility score (0–100) | Match report with gaps and strengths |
| 3. LEBENSLAUF | Adapts a master CV to the specific vacancy | ATS-optimized Markdown (DIN/single-column) |
| 4. ANSCHREIBEN | Generates a cover letter | DIN 5008 compliant, 1 A4 page, 4 paragraphs |
| 5. OUTPUT | Suggests file/folder naming convention | Softgarden, Workday, Personio compatible |

### ATS Scoring Formula (Textkernel-weighted)
```
ATS Score = (Job title match × 30) + (Tier1 skills% × 0.45) + (Tier2 skills% × 0.15) + 10
```
- **≥ 70** → Apply now
- **50–69** → Adapt CV first
- **< 50** → Skip vacancy

---

## Who Is This Model For

✅ **IT job seekers** applying to positions in Germany (2026 market)  
✅ **Career coaches and HR consultants** working with German ATS systems  
✅ **Developers** building job application automation pipelines  
✅ **Students and bootcamp graduates** entering the German IT market  
✅ **Non-native German speakers** who need DIN 5008-compliant documents  

---

## Key Features

- 🎯 **ATS-aware generation** — knows Workday, Personio, SAP SuccessFactors, Greenhouse, Softgarden/onlyfy, Lever, d.vinci, Recruitee
- 📋 **Structured JSON output** for Step 1 and Step 2 (machine-readable, pipeline-friendly)
- 🚫 **AI-language blacklist** — avoids generic AI phrases: *dynamisch, leidenschaftlich, begeistert, vielfältig, umfangreich* (common ATS red flags)
- ⏱️ **Recency Boosting** — weights recent experience (< 3 years) higher, following Textkernel ranking logic
- ⭐ **S.T.A.R. bullet format** — Situation + Task + Action (Technology) + Result (Number)
- 🏛️ **EU AI Act compliant** — enforces Human-in-the-Loop; model adapts, never invents facts
- 📄 **DIN 5008 cover letter** — correct German business letter format, no forbidden clichés
- 🔤 **Softgarden naming rules** — PDF filename must start with `CV_[Name]_[Firma]_Lebenslauf.pdf`

---

## Hardware Requirements

| Config | Min | Recommended |
|---|---|---|
| RAM | 4 GB | 8 GB |
| GPU | ❌ Not required | Any CUDA/ROCm GPU |
| CPU | Any x86-64 | 4+ physical cores |
| Disk | 2.2 GB | 2.2 GB |

**Optimized parameters for CPU-only (no GPU):**
```
num_gpu 0 | num_thread 4 | num_ctx 1024
num_batch 128 | mirostat 0 | temperature 0.10
```

Expected speed on Intel i5 (no GPU): **~4–8 tokens/sec**  
Expected speed on RTX 4070 (GPU): **~40–80 tokens/sec**

---

## Quick Start

```bash
# Pull and run:
ollama pull lelegioner/headhunter-public
ollama run lelegioner/headhunter-public

# Example prompt:
"Analysiere diese Stelle: IT-Systemadministrator bei Deutsche Telekom.
Anforderungen: Linux, Windows Server, Active Directory, Azure, Python."
```

### Expected response (Step 1):
```json
{
  "firma": "Deutsche Telekom",
  "stelle": "IT-Systemadministrator",
  "ats_system": "SAP SuccessFactors",
  "hard_skills_tier1": ["Linux", "Windows Server", "Active Directory", "Azure"],
  "hard_skills_tier2": ["Python", "Docker", "Monitoring"],
  ...
}
```

---

## Customize for Your Profile

This public version contains **placeholder fields** instead of personal data.  
To use it for your own job search, provide your profile in the first message:

```
MEIN PROFIL:
Name: [Your Name] | Email: [your@email.com] | Verfügbar: [Date]
Kenntnisse: [Your skills, comma-separated]
Erfahrung:
  [Date]-heute: [Role] | [Company] → [Technologies]
  [Date]-[Date]: [Role] | [Company] → [Technologies]

STELLENANZEIGE:
[Paste the full job posting here]
```

---

## Limitations

| Limitation | Details |
|---|---|
| **Context window: 1024 tokens** | Long job postings may be truncated. Summarize if > 800 words. |
| **3B parameter base model** | May produce less fluent German than 14B+ models. Always proofread. |
| **No internet access** | Cannot fetch job postings from URLs. Paste text directly. |
| **No PDF generation** | Outputs Markdown only. Use pandoc/wkhtmltopdf to convert. |
| **German market only** | Optimized for DE labor market, ATS systems, DIN 5008. Not suitable for US/UK applications. |
| **Human review required** | EU AI Act (Annex III): AI-generated CVs are High-Risk. Always verify before submitting. |
| **No real-time data** | Market knowledge frozen at training cutoff. Salary ranges may drift. |

---

## ❌ What This Model Is NOT For

- ❌ **General-purpose chat** — not optimized for conversation, coding help, or Q&A
- ❌ **Non-IT professions** — scoring formula calibrated for IT roles (Admin, DevOps, Dev)
- ❌ **Job markets outside Germany** — ATS logic, DIN norms, and Textkernel weights are DE-specific
- ❌ **Fully automated submissions** — always requires human review before sending (EU AI Act)
- ❌ **Generating fake experience** — strictly refuses to invent skills, dates, or employers
- ❌ **English-language applications** — cover letters and CVs are generated in German by default
- ❌ **Legal or HR compliance advice** — provides formatting guidance only, not legal counsel
- ❌ **Real-time job search** — cannot browse job boards or query APIs

---

## Ethics & Compliance

- **EU AI Act (Annex III):** CV screening and candidate selection tools are classified as **High-Risk AI systems**. This model is a *drafting assistant*, not a decision-maker. Final submission requires explicit human approval.
- **GDPR:** Do not include third-party personal data in prompts. The model does not store or transmit data.
- **Transparency:** Employers are not notified that documents were AI-assisted. Users are responsible for disclosure per applicable law.
- **No discrimination:** Model does not make recommendations based on age, gender, nationality, or health status.

---

## Full Project

The complete HeadHunter PROJECT_beta includes:
- `agent.py` — full automation pipeline (5-step workflow, SQLite logging, PDF generation)
- `Modelfile.cpu` / `Modelfile.template.gpu` — hardware-specific builds
- ATS database, skills map DE 2026, EU AI Act compliance guide
- Opencode CLI integration via MCP server

**Candidate profile in this public version:** replaced with placeholders — safe to share and adapt.

---

## License

Base model: **Meta Llama 3.2 Community License**  
System prompt and workflow logic: **MIT**  
Use of this model for job application automation is permitted under both licenses.
Commercial use requires registration with Meta per the Llama 3.2 Community License terms.
