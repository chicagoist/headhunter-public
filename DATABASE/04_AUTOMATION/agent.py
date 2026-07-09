"""
HeadHunter Agent v2.1
=====================
Автономный агент: анализирует вакансию → адаптирует Lebenslauf → создаöт Anschreiben → сохраняет пакет.

Режимы LLM (--mode):
  dry-run     Не использует LLM. Только Regex-анализ. Для тестирования.
  openrouter  БЕСПЛАТНО через OpenRouter API (нужен API-ключ с openrouter.ai)
  ollama      Локальный LLM через Ollama (ollama serve + ollama pull deepseek-r1:7b)
  api         OpenAI API (требует платный ключ)

Примеры:
    # Бесплатно (только нужен бесплатный API-ключ с openrouter.ai):
    python agent.py --vacancy vacancy.txt --mode openrouter --apikey sk-or-v1-...

    # Тест без LLM:
    python agent.py --vacancy vacancy.txt --mode dry-run

    # Локальная модель:
    python agent.py --vacancy vacancy.txt --mode ollama --model deepseek-r1:7b

    # OpenAI:
    python agent.py --vacancy vacancy.txt --mode api --apikey sk-...

Выходные файлы: OUTPUT/Bewerbungen/[DATUM]_[FIRMA]/
    lebenslauf_[firma].md
    lebenslauf_[firma].pdf   (если pandoc/wkhtmltopdf установлен)
    anschreiben_[firma].md
    ANALYSE_REPORT.md

Автор: HeadHunter PROJECT_beta v2.1 | 2026-07
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import io
from datetime import date, datetime
from pathlib import Path

# ── UTF-8 stdout для Windows ──────────────────────────────────────────────────
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ── Пути ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent.parent  # PROJECT_beta/
DATABASE_DIR = BASE_DIR / "DATABASE"
PROFILE_DIR  = DATABASE_DIR / "00_CANDIDATE_PROFILE"
OUTPUT_DIR   = BASE_DIR / "OUTPUT" / "Bewerbungen"
DB_PATH      = DATABASE_DIR / "05_DATABASE" / "ats_optimization.db"

KANDIDAT_PROFIL    = PROFILE_DIR / "kandidat_profil.md"
LEBENSLAUF_MASTER  = PROFILE_DIR / "lebenslauf_master.md"

# ── LLM Config ────────────────────────────────────────────────────────────────────────
OLLAMA_URL    = "http://localhost:11434"
# CPU-оптимизированная модель: i5-8365U, 4 ядра, 32 GB RAM, NO GPU
# Собрана: ollama create headhunter-cpu -f Modelfile.cpu  ✅
DEFAULT_MODEL = "headhunter-cpu"


# OpenRouter — только Google / Meta / OpenAI модели (по запросу пользователя)
# Gemma 4 31B первой — единственная ответившая в тесте
FREE_MODELS_PRIORITY = [
    "google/gemma-4-31b-it:free",              # ✅ Google Gemma 4 31B — отвечает!
    "google/gemma-4-26b-a4b-it:free",          # Google Gemma 4 26B
    "openai/gpt-oss-120b:free",                # OpenAI GPT-архитектура 120B
    "openai/gpt-oss-20b:free",                 # OpenAI GPT-архитектура 20B (быстрый)
    "meta-llama/llama-3.3-70b-instruct:free",  # Meta Llama 3.3 70B
    "meta-llama/llama-3.2-3b-instruct:free",   # Meta Llama 3.2 3B (лёгкий fallback)
]
OPENROUTER_URL          = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = FREE_MODELS_PRIORITY[0]  # google/gemma-4-31b-it:free


# ═════════════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═════════════════════════════════════════════════════════════════════════════

def slugify(text: str, maxlen: int = 20) -> str:
    """Преобразует текст в безопасное имя файла."""
    text = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE)
    text = re.sub(r'[\s]+', '_', text.strip())
    return text[:maxlen]


def load_file(path: Path) -> str:
    """Читает файл в строку."""
    if not path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    return path.read_text(encoding='utf-8')


def save_file(path: Path, content: str) -> None:
    """Создаёт директорию при необходимости и сохраняет файл."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"  [GESPEICHERT] {path.relative_to(BASE_DIR)}")


def md_to_html(md_text: str) -> str:
    """Простой Markdown → HTML конвертер для PDF-генерации."""
    import html as html_module
    lines = md_text.split('\n')
    html_lines = []
    in_ul = False
    html_lines.append("""<!DOCTYPE html><html><head><meta charset='utf-8'>
<style>
  body{font-family:Arial,sans-serif;font-size:11pt;margin:2cm;color:#111;line-height:1.45}
  h1{font-size:16pt;border-bottom:2px solid #333;padding-bottom:4px;margin-top:0}
  h2{font-size:13pt;border-bottom:1px solid #aaa;margin-top:18px}
  h3{font-size:11pt;margin-top:12px}
  ul{margin:4px 0;padding-left:20px} li{margin:2px 0}
  hr{border:1px solid #ccc}
  table{border-collapse:collapse;width:100%;margin:8px 0}
  td,th{border:1px solid #ccc;padding:4px 8px;text-align:left}
  th{background:#eee;font-weight:bold}
  strong{font-weight:bold} em{font-style:italic}
</style></head><body>""")
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('### '):
            if in_ul: html_lines.append('</ul>'); in_ul = False
            html_lines.append(f'<h3>{html_module.escape(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            if in_ul: html_lines.append('</ul>'); in_ul = False
            html_lines.append(f'<h2>{html_module.escape(stripped[3:])}</h2>')
        elif stripped.startswith('# '):
            if in_ul: html_lines.append('</ul>'); in_ul = False
            html_lines.append(f'<h1>{html_module.escape(stripped[2:])}</h1>')
        elif stripped.startswith('- ') or stripped.startswith('* '):
            if not in_ul: html_lines.append('<ul>'); in_ul = True
            content = html_module.escape(stripped[2:])
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            html_lines.append(f'<li>{content}</li>')
        elif stripped == '---' or stripped == '___':
            if in_ul: html_lines.append('</ul>'); in_ul = False
            html_lines.append('<hr>')
        elif stripped == '':
            if in_ul: html_lines.append('</ul>'); in_ul = False
            html_lines.append('<br>')
        else:
            if in_ul: html_lines.append('</ul>'); in_ul = False
            content = html_module.escape(stripped)
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
            html_lines.append(f'<p style="margin:3px 0">{content}</p>')
    if in_ul: html_lines.append('</ul>')
    html_lines.append('</body></html>')
    return '\n'.join(html_lines)


def generate_pdf(md_path: Path, pdf_path: Path) -> bool:
    """Конвертирует Markdown в PDF через pandoc, wkhtmltopdf или weasyprint."""
    # Попытка 1: pandoc + wkhtmltopdf
    try:
        result = subprocess.run(
            ["pandoc", str(md_path), "-o", str(pdf_path),
             "--pdf-engine=wkhtmltopdf",
             "--variable=geometry:margin=2cm",
             "--variable=fontsize=11pt"],
            capture_output=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  [PDF] Erstellt mit pandoc+wkhtmltopdf: {pdf_path.name}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Попытка 2: wkhtmltopdf direkt (MD→HTML→PDF)
    html_path = None
    try:
        html_path = pdf_path.with_suffix('.html')
        html_content = md_to_html(md_path.read_text(encoding='utf-8'))
        html_path.write_text(html_content, encoding='utf-8')
        result = subprocess.run(
            ["wkhtmltopdf",
             "--quiet",
             "--margin-top", "20mm", "--margin-bottom", "20mm",
             "--margin-left", "20mm", "--margin-right", "20mm",
             "--encoding", "utf-8",
             str(html_path), str(pdf_path)],
            capture_output=True, timeout=60
        )
        if result.returncode == 0:
            print(f"  [PDF] Erstellt mit wkhtmltopdf: {pdf_path.name}")
            return True
        else:
            print(f"  [WARNUNG] wkhtmltopdf Fehler: {result.stderr.decode(errors='replace')[:200]}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception as e:
        print(f"  [WARNUNG] wkhtmltopdf direkt fehlgeschlagen: {e}")
    finally:
        if html_path is not None:
            html_path.unlink(missing_ok=True)

    # Попытка 3: weasyprint
    try:
        import weasyprint
        html_content = md_to_html(md_path.read_text(encoding='utf-8'))
        weasyprint.HTML(string=html_content).write_pdf(str(pdf_path))
        print(f"  [PDF] Erstellt mit weasyprint: {pdf_path.name}")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"  [WARNUNG] weasyprint fehlgeschlagen: {e}")

    print("  [INFO] PDF-Engine nicht verfügbar. Nur MD gespeichert.")
    print("         Tipp: pandoc ist installiert aber wkhtmltopdf evtl. nicht im PATH?")
    return False


# ═════════════════════════════════════════════════════════════════════════════
# LLM KOMMUNIKATION
# ═════════════════════════════════════════════════════════════════════════════

def call_ollama(prompt: str, system: str, model: str = DEFAULT_MODEL) -> str:
    """Вызов локального Ollama LLM."""
    try:
        import httpx
    except ImportError:
        print("[FEHLER] httpx nicht installiert: pip install httpx")
        sys.exit(1)
    try:
        resp = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.25, "top_p": 0.9},
            },
            timeout=180.0,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        print(f"[FEHLER] Ollama: {e}")
        print("  Pruefen: ollama serve && ollama pull deepseek-r1:7b")
        sys.exit(1)


def call_openai_compat(
    prompt: str,
    system: str,
    api_key: str,
    model: str,
    base_url: str = "https://api.openai.com/v1/chat/completions",
) -> str:
    """Универсальный клиент для OpenAI-совместимых API (Mistral, GROQ, и др.)."""
    try:
        import httpx
    except ImportError:
        print("[FEHLER] httpx nicht installiert: pip install httpx")
        sys.exit(1)
    if not api_key:
        print(f"[FEHLER] API-Key fehlt fuer {base_url}")
        sys.exit(1)
    try:
        print(f"     [{base_url.split('/')[2]}] Modell: {model}")
        resp = httpx.post(
            base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                "temperature": 0.25,
                "max_tokens": 4096,
            },
            timeout=90.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            print(f"[FEHLER] API Fehler: {data['error'].get('message','')[:200]}")
            sys.exit(1)
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        if usage:
            print(f"     [OK] Tokens: {usage.get('prompt_tokens','-')} in / {usage.get('completion_tokens','-')} out")
        return content
    except Exception as e:
        print(f"[FEHLER] {base_url}: {e}")
        sys.exit(1)


def call_openai_api(prompt: str, system: str, api_key: str, model: str = "gpt-4o-mini") -> str:
    """Вызов OpenAI API."""
    try:
        import httpx
    except ImportError:
        print("[FEHLER] httpx nicht installiert: pip install httpx")
        sys.exit(1)
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                "temperature": 0.25,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[FEHLER] OpenAI API: {e}")
        sys.exit(1)


def call_openrouter(
    prompt: str,
    system: str,
    api_key: str,
    model: str = DEFAULT_OPENROUTER_MODEL
) -> str:
    """Вызов OpenRouter API с авто-fallback по всем бесплатным моделям.

    При 429 (rate limit) или 502 (провайдер недоступен) автоматически
    переключается на следующую модель из FREE_MODELS_PRIORITY.

    Как получить бесплатный ключ:
      1. https://openrouter.ai -> Sign up -> Keys -> Create Key
      2. 200 запросов/день бесплатно
    """
    try:
        import httpx
        import time as _time
    except ImportError:
        print("[FEHLER] httpx nicht installiert: pip install httpx")
        sys.exit(1)

    if not api_key:
        print("[FEHLER] OpenRouter API-Key fehlt!")
        print("  Kostenlos: https://openrouter.ai -> Keys -> Create Key")
        print("  Dann: --apikey sk-or-v1-...")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/HeadHunter-Agent",
        "X-Title": "HeadHunter-Agent-v2.1",
        "Content-Type": "application/json",
    }

    # Попытки: запрошенная модель первой, затем все остальные из приоритетного списка
    models_to_try = [model] + [m for m in FREE_MODELS_PRIORITY if m != model]

    for attempt_model in models_to_try:
        payload = {
            "model": attempt_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            "temperature": 0.25,
            "max_tokens": 4096,
        }
        try:
            print(f"     [OpenRouter] Trying: {attempt_model}")
            resp = httpx.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=120.0,
            )

            if resp.status_code in (429, 502, 503):
                err_body = ""
                try:
                    err_body = resp.json().get("error", {}).get("message", "")[:100]
                except Exception:
                    err_body = resp.text[:100]
                print(f"     [SKIP {resp.status_code}] {err_body}")
                _time.sleep(5)
                continue

            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                print(f"     [SKIP] {data['error'].get('message','')[:100]}")
                _time.sleep(5)
                continue

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            if usage:
                print(f"     [OK] {attempt_model} | Tokens: {usage.get('prompt_tokens','-')} in / {usage.get('completion_tokens','-')} out")
            return content

        except httpx.HTTPStatusError as e:
            print(f"     [SKIP {e.response.status_code}] {attempt_model}")
            _time.sleep(5)
            continue
        except Exception as e:
            print(f"     [ERROR] {attempt_model}: {str(e)[:80]}")
            _time.sleep(3)
            continue

    # Все модели недоступны
    print("\n[FEHLER] Alle OpenRouter-Modelle sind aktuell rate-limited (429).")
    print("  Loesungen:")
    print("  1. 10-15 Minuten warten und erneut versuchen (Abendspitze)")
    print("  2. Am naechsten Tag versuchen (200 Req/Tag Limit)")
    print("  3. Jetzt testen: --mode dry-run")
    print("  4. 10 Credits aufladen: https://openrouter.ai/credits")
    sys.exit(1)




# ═════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Du bist ein erfahrener IT-Recruiter, Headhunter und Karrierecoach 
für den deutschen Arbeitsmarkt 2026. Du kennst:
- ATS-Systeme (Workday, Personio, SAP SuccessFactors, Greenhouse, Lever)
- DIN SPEC 91426, ISO 10667, EU AI Act (High-Risk HR-Systeme)
- Semantisches Keyword-Matching und ATS-Bypass-Strategien
- Deutsche Bewerbungsstandards (DIN 5008, Lebenslauf-Konventionen)
- IT-Markt Deutschland: Jobrollen, Tech-Stacks, Gehaltsstrukturen

Deine Antworten sind:
- Präzise und umsetzbar (keine allgemeinen Ratschläge)
- Auf Fakten basierend (erfinde keine Erfahrungen oder Daten)
- Im Sinne von "Human-in-the-Loop" — du adaptierst, nicht erfindest
- Auf DEUTSCH (Bewerbungsdokumente) und RUSSISCH (Reports/Analyse)"""


# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — VACANCY ANALYSE
# ═════════════════════════════════════════════════════════════════════════════

def build_analysis_prompt(vacancy_text: str) -> str:
    return f"""Analysiere die Stellenanzeige. Antworte NUR mit JSON, kein Text davor/danach.

STELLENANZEIGE:
{vacancy_text}

JSON-Format (alle Felder ausfullen, null wenn unbekannt):
{{"firma":"Name","stelle":"exakter Jobtitel","ort":"Ort","remote":"hybrid","sprache_bewerbung":"DE","ats_system":"Unknown","ansprechpartner":null,"referenz_nr":null,"hard_skills_tier1":["skill1","skill2"],"hard_skills_tier2":["skill3"],"soft_skills":["soft1"],"besonderheiten":[],"gehalt_erwartet":null}}"""


# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — MATCH & SCORE
# ═════════════════════════════════════════════════════════════════════════════

def build_match_prompt(vacancy_json: dict, kandidat_profil: str) -> str:
    # Nur die relevanten Teile des Profils senden (Kenntnisse + Zertifikate)
    profil_short = kandidat_profil[:2000]  # max 2000 Zeichen
    return f"""Berechne ATS Match Score. Antworte NUR mit JSON.

KANDIDAT-KENNTNISSE (Auszug):
{profil_short}

STELLE: {vacancy_json.get('stelle')} bei {vacancy_json.get('firma')}
Tier1 (Pflicht): {vacancy_json.get('hard_skills_tier1', [])}
Tier2 (Wunsch): {vacancy_json.get('hard_skills_tier2', [])}

Formula: ATS = (T1_match_pct*0.55)+(T2_match_pct*0.25)+20
Entscheidung: >=70=JETZT_BEWERBEN, 50-69=ANPASSEN, <50=UEBERSPRINGEN

{{"ats_score":75,"tier1_score":80,"tier2_score":60,"tier1_vorhanden":["kw1"],"tier1_fehlend":["kw2"],"tier2_vorhanden":["kw3"],"tier2_fehlend":["kw4"],"staerken":["Stärke1","Stärke2","Stärke3"],"red_flags":["Flag1"],"empfehlung":"JETZT_BEWERBEN","empfehlung_begruendung":"kurze Begründung"}}"""


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — LEBENSLAUF ADAPT
# ═════════════════════════════════════════════════════════════════════════════

def build_lebenslauf_prompt(vacancy_json: dict, match_json: dict, lebenslauf_master: str) -> str:
    return f"""AUFGABE STEP 3: Adaptiere den Lebenslauf für diese Stelle.

ZIELSTELLE: {vacancy_json.get('stelle')} bei {vacancy_json.get('firma')}
FEHLENDE TIER1-KEYWORDS (einzubauen falls Kandidat sie kann): {match_json.get('tier1_fehlend', [])}
TIER1-KEYWORDS (Reihenfolge in Kenntnisse nach oben): {match_json.get('tier1_vorhanden', [])}

MASTER-LEBENSLAUF:
---
{lebenslauf_master}
---

STRIKTE REGELN:
1. NICHT ändern: Firmennamen, Daten, Zertifikatsnamen, Kontaktdaten
2. Profil-Abschnitt: spiegelt den Jobtitel "{vacancy_json.get('stelle')}" wider
3. Kenntnisse: Tier1-Keywords ganz oben in jeweiliger Kategorie
4. Bullet Points: [Aktionsverb] + [Technologie] + [Kontext/Ergebnis]
5. Fehlende Keywords NUR einbauen wenn Kandidat sie tatsächlich hat
6. Single-Column Markdown, max 2 A4-Seiten äquivalent
7. Kein Tabellen-Markup in Kernabschnitten (ATS-Parsing!)

Gib den VOLLSTÄNDIGEN adaptierten Lebenslauf als Markdown aus.
Beginne direkt mit deinem Namen (z.B. "# MAX MUSTERMANN") — kein Präambel-Text."""


# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — ANSCHREIBEN
# ═════════════════════════════════════════════════════════════════════════════

def build_anschreiben_prompt(vacancy_json: dict, match_json: dict, kandidat_profil: str) -> str:
    heute = date.today().strftime("%d.%m.%Y")
    ansprechpartner = vacancy_json.get('ansprechpartner') or 'Damen und Herren'
    anrede = f"Sehr geehrte/r {ansprechpartner}," if vacancy_json.get('ansprechpartner') else "Sehr geehrte Damen und Herren,"
    ref = f" — Ref.-Nr.: {vacancy_json['referenz_nr']}" if vacancy_json.get('referenz_nr') else ""

    return f"""AUFGABE STEP 4: Erstelle ein vollständiges deutsches Anschreiben (DIN 5008).

ZIELSTELLE: {vacancy_json.get('stelle')} bei {vacancy_json.get('firma')}
ORT: {vacancy_json.get('ort')}
DATUM: {heute}
ANSPRECHPARTNER: {ansprechpartner}
TIER1-KEYWORDS (organisch einbauen): {match_json.get('tier1_vorhanden', [])}
SOFT SKILLS AUS ANZEIGE: {vacancy_json.get('soft_skills', [])}
BESONDERHEITEN: {vacancy_json.get('besonderheiten', [])}

TRANSFER-ARGUMENTE (wähle 1-2 passende aus — passe an dein Profil an!):
- [BEISPIEL: Frühere Erfahrung → Transfer in IT-Kompetenz]
- [BEISPIEL: Andere Branche → relevante IT-Eigenschaft]

KANDIDAT-KURZPROFIL:
{kandidat_profil[:500]}

REGELN:
- KEIN "Hiermit bewerbe ich mich..." — direkter Hook!
- Firmenspezifischer Einstieg (warum genau DIESE Firma)
- Soft Skills durch konkretes Beispiel BEWEISEN, nicht behaupten
- Verfügbar ab: laut kandidat_profil.md
- Genau 1 A4-Seite, 4 Absätze
- Keine generischen KI-Phrasen

Ausgabe-Format: vollständiges Anschreiben als Markdown.
Beginne mit dem Absenderblock:

---
[VORNAME NACHNAME]  
[STRASSE, PLZ STADT]  
Telefon: [TELEFON]  
E-Mail: [EMAIL]  
LinkedIn: [LINKEDIN-URL]
---
[dann rechts: {heute}]

{vacancy_json.get('firma', '[Firma]')}  
[Adresse der Firma — Platzhalter]

**Bewerbung als {vacancy_json.get('stelle', '[Stelle]')}{ref}**

{anrede}

[EINLEITUNG — Hook 3-4 Zeilen]

[HAUPTTEIL 1 — Hard Skills / IT-Fachkenntnisse 4-6 Zeilen]

[HAUPTTEIL 2 — Soft Skills Transfer 3-5 Zeilen]

[SCHLUSS — Verfügbarkeit + Call to Action 2-3 Zeilen]

Mit freundlichen Grüßen,

[VORNAME NACHNAME]

Anlagen: Lebenslauf, Zertifikate, Empfehlungsschreiben"""


# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — SAVE OUTPUT & DB LOG
# ═════════════════════════════════════════════════════════════════════════════

def clean_llm_output(text: str, doc_type: str = "generic") -> str:
    """Очищает вывод LLM: убирает ```markdown``` обёртки и лишние примечания."""
    # Убрать markdown code fences в начале и конце
    text = re.sub(r'^```(?:markdown|md)?\s*\n?', '', text.strip())
    text = re.sub(r'\n?```\s*$', '', text.strip())
    text = text.strip()

    if doc_type == "anschreiben":
        # Отрезать внутренние заметки LLM — только ПОСЛЕ подписи кандидата.
        # Паттерны для обнаружения конца письма + начала мусора:
        cutoff_patterns = [
            # После подписи — блок ATS-анализа через ---
            r'([A-ZÄÖÜ][a-zäöüß]+ [A-ZÄÖÜ][a-zäöüß]+\b.*?\n)\n---\n',
            # Прямые маркеры внутреннего анализа
            r'\n\*\*ATS-Optimierungshinweise',
            r'\nATS-Optimierungs',
            r'\n\*Für russische Analyse',
            r'\n---\n\*\*ATS',
            r'\n\[INTERN\]',
        ]
        for pat in cutoff_patterns:
            m = re.search(pat, text, re.DOTALL)
            if m:
                cut_at = m.end(1) if m.lastindex and m.lastindex >= 1 else m.start()
                if cut_at > 500:
                    text = text[:cut_at].rstrip()
                    break

    # Финальная очистка: убрать любые оставшиеся закрывающие ``` в конце
    text = re.sub(r'\n?```\s*$', '', text.strip())
    return text


def save_output_package(
    vacancy_json: dict,
    match_json: dict,
    lebenslauf_text: str,
    anschreiben_text: str,
) -> Path:
    """Сохраняет все файлы пакета в OUTPUT/Bewerbungen/"""
    today_str = date.today().isoformat()
    firma_slug = slugify(vacancy_json.get('firma', 'Unbekannt'))
    stelle_slug = slugify(vacancy_json.get('stelle', 'Stelle'), maxlen=15)
    folder_name = f"{today_str}_{firma_slug}_{stelle_slug}"
    out_dir = OUTPUT_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)

    lv_md   = out_dir / f"lebenslauf_{firma_slug}.md"
    lv_pdf  = out_dir / f"lebenslauf_{firma_slug}.pdf"
    ans_md  = out_dir / f"anschreiben_{firma_slug}.md"
    rep_md  = out_dir / "ANALYSE_REPORT.md"

    # Lebenslauf MD
    save_file(lv_md, clean_llm_output(lebenslauf_text, "lebenslauf"))

    # Anschreiben MD — убрать обёртки и внутренние заметки LLM
    save_file(ans_md, clean_llm_output(anschreiben_text, "anschreiben"))

    # PDF
    generate_pdf(lv_md, lv_pdf)

    # Analyse-Report
    report = f"""# Analyse-Report: {vacancy_json.get('stelle')} @ {vacancy_json.get('firma')}

**Datum:** {today_str}  
**ATS Score:** {match_json.get('ats_score', 'N/A')}/100  
**Empfehlung:** {match_json.get('empfehlung', 'N/A')}  
**Begründung:** {match_json.get('empfehlung_begruendung', '')}

## Keyword Match

| Tier | Vorhanden | Fehlend |
|---|---|---|
| Tier 1 (Pflicht) | {', '.join(match_json.get('tier1_vorhanden', []))} | {', '.join(match_json.get('tier1_fehlend', []))} |
| Tier 2 (Wunsch) | {', '.join(match_json.get('tier2_vorhanden', []))} | {', '.join(match_json.get('tier2_fehlend', []))} |

## Stärken
{chr(10).join(f'- {s}' for s in match_json.get('staerken', []))}

## Red Flags
{chr(10).join(f'- {r}' for r in match_json.get('red_flags', []))}

## Dateien
- `{lv_md.name}` — Angepasster Lebenslauf
- `{ans_md.name}` — Anschreiben
- `{lv_pdf.name}` — PDF (falls erstellt)
"""
    save_file(rep_md, report)

    return out_dir


def log_to_db(vacancy_json: dict, match_json: dict, out_dir: Path) -> None:
    """Записывает отклик в SQLite базу данных."""
    if not DB_PATH.exists():
        print("  [INFO] DB nicht gefunden, kein Log. Zuerst setup_ats_db.py ausfuehren.")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()

        # Company
        cur.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)",
                    (vacancy_json.get('firma', 'Unknown'),))
        company_id = cur.execute("SELECT company_id FROM companies WHERE name = ?",
                                 (vacancy_json.get('firma', 'Unknown'),)).fetchone()[0]

        # Vacancy
        cur.execute("""INSERT INTO vacancies
            (company_id, job_title, location, remote_option, date_found)
            VALUES (?, ?, ?, ?, date('now'))""",
            (company_id,
             vacancy_json.get('stelle', ''),
             vacancy_json.get('ort', ''),
             vacancy_json.get('remote', '')))
        vacancy_id = cur.lastrowid

        # CV iteration
        cur.execute("""INSERT INTO cv_iterations
            (vacancy_id, cv_file_path, ats_score, human_reviewed, ai_tools_used)
            VALUES (?, ?, ?, 1, 'HeadHunter-Agent-v2')""",
            (vacancy_id,
             str(out_dir),
             match_json.get('ats_score', 0)))
        iter_id = cur.lastrowid

        # Application
        cur.execute("""INSERT INTO applications
            (iteration_id, application_date, status)
            VALUES (?, date('now'), 'PENDING')""",
            (iter_id,))

        conn.commit()
        conn.close()
        print("  [DB] Eintrag in ats_optimization.db gespeichert.")
    except Exception as e:
        print(f"  [WARNUNG] DB-Log fehlgeschlagen: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# DRY-RUN HILFSFUNKTION
# ═════════════════════════════════════════════════════════════════════════════

def _dry_run_parse(prompt: str, kandidat_profil: str) -> str:
    """Simuliert LLM-Antwort im dry-run Modus mittels Regex-Parsing."""

    if '"hard_skills_tier1"' in prompt or 'STEP 1' in prompt or 'Stellenanzeige' in prompt:
        # STEP 1 — Vacancy-Parsing via Regex aus dem tatsächlichen Prompt
        vacancy_text = prompt
        # Firma
        firma_match = re.search(r'(?:Unternehmen|Firma|Company)[:\s]+([^\n]{3,60})', vacancy_text, re.IGNORECASE)
        firma = firma_match.group(1).strip() if firma_match else 'Unbekannte Firma'
        # Stelle
        stelle_match = re.search(r'^([^\n]{5,80}(?:Administrator|Entwickler|Engineer|Manager|Analyst|Spezialist|Techniker|Consultant|Developer|Admin|Support)[^\n]{0,40})', vacancy_text, re.MULTILINE|re.IGNORECASE)
        stelle = stelle_match.group(1).strip() if stelle_match else 'IT-Position'
        # Remote
        remote = 'hybrid' if re.search(r'hybrid|home.?office|remote', vacancy_text, re.I) else \
                 'remote'   if re.search(r'\bremote\b|100%.*remote', vacancy_text, re.I) else 'onsite'
        # Ort
        ort_match = re.search(r'(?:Standort|Ort|Location)[:\s]+([^\n]{3,50})', vacancy_text, re.IGNORECASE)
        ort = ort_match.group(1).strip() if ort_match else 'Deutschland'
        # Ansprechpartner
        ap_match = re.search(r'(?:Ansprechpartner[^\n:]*|Kontakt)[:\s]+([^\n]{3,60})', vacancy_text, re.IGNORECASE)
        ap = ap_match.group(1).strip() if ap_match else None
        # Referenz
        ref_match = re.search(r'(?:Ref(?:erenz)?(?:[-.\s]Nr\.?)?)[:\s]*([A-Z0-9\-]{4,20})', vacancy_text, re.IGNORECASE)
        ref = ref_match.group(1).strip() if ref_match else None
        # Gehalt
        gehalt_match = re.search(r'(\d[\d.,]+)\s*[–\-]\s*(\d[\d.,]+)\s*(?:€|EUR|Tsd)', vacancy_text)
        gehalt = f"{gehalt_match.group(1)}–{gehalt_match.group(2)} €" if gehalt_match else None

        # Keywords aus "Muss:" Sektion
        tier1 = []
        tier2 = []
        muss_block = re.search(r'(?:Muss|Pflicht|Voraussetzung|Anforderung)[:\s]*\n((?:[-•*]\s*.+\n?){1,15})', vacancy_text, re.IGNORECASE)
        wunsch_block = re.search(r'(?:W[üu]nschenswert|Nice.to.have|Optional|Von Vorteil)[:\s]*\n((?:[-•*]\s*.+\n?){1,12})', vacancy_text, re.IGNORECASE)

        if muss_block:
            for line in muss_block.group(1).split('\n'):
                kw = re.sub(r'^[-•*]\s*', '', line).strip()
                if 5 < len(kw) < 80:
                    tier1.append(kw[:60])
        if wunsch_block:
            for line in wunsch_block.group(1).split('\n'):
                kw = re.sub(r'^[-•*]\s*', '', line).strip()
                if 5 < len(kw) < 80:
                    tier2.append(kw[:60])

        # Fallback wenn keine Blöcke gefunden
        if not tier1:
            tier1 = ["Windows Server", "Linux", "Netzwerk", "Active Directory", "PowerShell"]
        if not tier2:
            tier2 = ["Docker", "Python", "Azure", "Cisco"]

        result = {
            "firma": firma,
            "stelle": stelle.strip('.,- '),
            "ort": ort,
            "remote": remote,
            "sprache_bewerbung": "DE",
            "ats_system": "Unknown",
            "ansprechpartner": ap,
            "referenz_nr": ref,
            "hard_skills_tier1": tier1[:10],
            "hard_skills_tier2": tier2[:8],
            "soft_skills": ["Eigenverantwortung", "Kommunikationsstärke", "Teamfähigkeit"],
            "besonderheiten": [],
            "gehalt_erwartet": gehalt,
        }
        return json.dumps(result, ensure_ascii=False)

    elif '"ats_score"' in prompt or 'STEP 2' in prompt or 'Kandidatenprofil' in prompt.lower():
        # STEP 2 — Einfacher Regex-Match zwischen Profil und Tier1/Tier2
        # Tier1/Tier2 aus dem Prompt extrahieren (Python repr oder JSON Format)
        def parse_list_from_prompt(pattern: str, text: str) -> list:
            m = re.search(pattern, text, re.DOTALL)
            if not m: return []
            raw = m.group(1).strip()
            # Normalisiere: ersetze einzelne Anführungszeichen durch doppelte
            raw = raw.replace("'", '"')
            try:
                return json.loads(raw)
            except Exception:
                # Fallback: extrahiere alles zwischen Anführungszeichen
                return re.findall(r'"([^"]{3,80})"', raw)

        tier1 = parse_list_from_prompt(r'Tier1 \(Pflicht\):\s*(\[.+?\])', prompt)
        tier2 = parse_list_from_prompt(r'Tier2 \(Wunsch\):\s*(\[.+?\])', prompt)

        # Match gegen Profil
        profil_lower = kandidat_profil.lower()
        t1_ok  = [k for k in tier1 if k.lower().split()[0] in profil_lower]
        t1_no  = [k for k in tier1 if k not in t1_ok]
        t2_ok  = [k for k in tier2 if k.lower().split()[0] in profil_lower]
        t2_no  = [k for k in tier2 if k not in t2_ok]

        t1_pct = (len(t1_ok)/len(tier1)*100) if tier1 else 0
        t2_pct = (len(t2_ok)/len(tier2)*100) if tier2 else 0
        score  = round(t1_pct * 0.55 + t2_pct * 0.25 + 20)
        score  = min(score, 100)

        if score >= 70:
            empf = "JETZT_BEWERBEN"
            beg  = "[DRY-RUN] Score ausreichend für Direktbewerbung"
        elif score >= 50:
            empf = "ANPASSEN"
            beg  = f"[DRY-RUN] {len(t1_no)} Tier1-Keywords fehlen noch"
        else:
            empf = "UEBERSPRINGEN"
            beg  = "[DRY-RUN] Zu großer Gap bei Pflicht-Skills"

        result = {
            "ats_score": score,
            "tier1_score": round(t1_pct),
            "tier2_score": round(t2_pct),
            "tier1_vorhanden": t1_ok,
            "tier1_fehlend": t1_no,
            "tier2_vorhanden": t2_ok,
            "tier2_fehlend": t2_no,
            "staerken": ["Weiterbildung Zukunftsmotor 2026", "10 Jahre Sysadmin-Erfahrung", "Deutsch B2+"],
            "red_flags": t1_no[:2] if t1_no else [],
            "empfehlung": empf,
            "empfehlung_begruendung": beg,
        }
        return json.dumps(result, ensure_ascii=False)

    else:
        # STEP 3/4 — Lebenslauf/Anschreiben im Dry-Run: gibt Platzhalter zurück
        return "[DRY-RUN PLACEHOLDER — kein LLM aktiv]"


# ═════════════════════════════════════════════════════════════════════════════
# JSON EXTRAKTION
# ═════════════════════════════════════════════════════════════════════════════

def extract_json(text: str) -> dict:
    """Извлекает JSON из ответа LLM. Умеет чинить обрезанные ответы."""
    # Убрать markdown-блоки кода
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```', '', text)
    text = text.strip()

    # Найти начало JSON-объекта
    start = text.find('{')
    if start == -1:
        raise ValueError("Kein JSON-Objekt in Antwort gefunden.")
    json_text = text[start:]

    # Попытка 1: полный парсинг
    end = json_text.rfind('}') + 1
    if end > 0:
        try:
            return json.loads(json_text[:end])
        except json.JSONDecodeError:
            pass

    # Попытка 2: JSON обрезан — закрыть открытые структуры
    repaired = json_text
    # Убрать незавершённую последнюю строку (обрезана на середине)
    repaired = re.sub(r',?\s*"[^"]*$', '', repaired)   # неполный ключ
    repaired = re.sub(r',?\s*"[^"]+":\s*"[^"]*$', '', repaired)  # неполное значение
    repaired = re.sub(r',?\s*"[^"]+":\s*\[$', '', repaired)       # незакрытый массив
    repaired = re.sub(r',?\s*$', '', repaired)           # висящая запятая
    # Закрыть все незакрытые массивы и объекты
    open_brackets = repaired.count('[') - repaired.count(']')
    open_braces   = repaired.count('{') - repaired.count('}')
    repaired += ']' * max(0, open_brackets)
    repaired += '}' * max(0, open_braces)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON konnte nicht repariert werden: {e}\nRohantwort (250 Zeichen):\n{text[:250]}")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="HeadHunter Agent v2.1 — Bewerbungspaket-Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  Kostenlos (OpenRouter):  python agent.py --vacancy stelle.txt --mode openrouter --apikey sk-or-v1-...
  Lokal (Ollama):          python agent.py --vacancy stelle.txt --mode ollama
  Test (kein LLM):         python agent.py --vacancy stelle.txt --mode dry-run
  OpenAI:                  python agent.py --vacancy stelle.txt --mode api --apikey sk-...
"""
    )
    parser.add_argument("--vacancy", required=True,
                        help="Pfad zur Stellenanzeige (TXT-Datei)")
    parser.add_argument("--mode",
                        choices=["openrouter", "ollama", "api", "mistral", "dry-run"],
                        default="openrouter",
                        help=("LLM-Modus: "
                              "openrouter = Google/Meta/GPT via openrouter.ai (empfohlen), "
                              "mistral = Mistral AI (MISTRAL_API_KEY), "
                              "ollama = lokal, "
                              "api = OpenAI, "
                              "dry-run = kein LLM (Test)"))
    parser.add_argument("--model", default=None,
                        help=(f"Modellname. Defaults: "
                              f"openrouter=>{DEFAULT_OPENROUTER_MODEL}, "
                              f"ollama=>{DEFAULT_MODEL}, "
                              f"api=>gpt-4o-mini"))
    parser.add_argument("--apikey",
                        default=None,
                        help=("API-Key je nach Modus. "
                              "Wird automatisch aus Umgebungsvariablen gelesen: "
                              "OPENROUTER_API_KEY, MISTRAL_API_KEY, OPENAI_API_KEY."))
    args = parser.parse_args()

    # Modell-Defaults je nach Modus
    if args.model is None:
        if args.mode == "openrouter":
            args.model = DEFAULT_OPENROUTER_MODEL
        elif args.mode == "api":
            args.model = "gpt-4o-mini"
        elif args.mode == "mistral":
            args.model = "mistral-large-latest"
        else:
            args.model = DEFAULT_MODEL

    # API-Key: --apikey hat Priorität, sonst aus Umgebungsvariablen
    if not args.apikey:
        if args.mode == "openrouter":
            args.apikey = os.getenv("OPENROUTER_API_KEY", "")
        elif args.mode == "mistral":
            args.apikey = os.getenv("MISTRAL_API_KEY", "")
        elif args.mode == "api":
            args.apikey = os.getenv("OPENAI_API_KEY", "")


    # LLM-Wrapper
    def llm(prompt: str, system: str = SYSTEM_PROMPT) -> str:
        if args.mode == "ollama":
            return call_ollama(prompt, system, args.model)
        elif args.mode == "api":
            if not args.apikey:
                print("[FEHLER] --apikey fehlt oder OPENAI_API_KEY nicht gesetzt.")
                sys.exit(1)
            return call_openai_api(prompt, system, args.apikey, args.model)
        elif args.mode == "openrouter":
            return call_openrouter(prompt, system, args.apikey, args.model)
        elif args.mode == "mistral":
            return call_openai_compat(
                prompt, system, args.apikey, args.model,
                base_url="https://api.mistral.ai/v1/chat/completions"
            )
        else:  # dry-run
            return _dry_run_parse(prompt, kandidat_profil)

    print("\n" + "=" * 60)
    print("  HeadHunter Agent v2.1")
    print("=" * 60)

    # Загрузка данных
    print("\n[1/5] Lade Kandidatenprofil und Lebenslauf-Vorlage...")
    kandidat_profil   = load_file(KANDIDAT_PROFIL)
    lebenslauf_master = load_file(LEBENSLAUF_MASTER)
    vacancy_text      = load_file(Path(args.vacancy))
    print("     OK")

    # STEP 1 — Анализ вакансии
    print("\n[2/5] STEP 1 — Vacancy-Analyse...")
    raw1 = llm(build_analysis_prompt(vacancy_text))
    try:
        vacancy_json = extract_json(raw1)
    except Exception as e:
        print(f"  [FEHLER] JSON-Parse fehlgeschlagen: {e}")
        print(f"  Rohantwort: {raw1[:300]}")
        sys.exit(1)
    print(f"     Firma: {vacancy_json.get('firma')} | Stelle: {vacancy_json.get('stelle')}")

    # STEP 2 — Match Score
    print("\n[3/5] STEP 2 — Match & Score...")
    raw2 = llm(build_match_prompt(vacancy_json, kandidat_profil))
    try:
        match_json = extract_json(raw2)
    except Exception as e:
        print(f"  [FEHLER] {e} — Fallback auf leere Match-Daten")
        match_json = {"ats_score": 0, "tier1_vorhanden": [], "tier1_fehlend": [],
                      "tier2_vorhanden": [], "tier2_fehlend": [], "staerken": [],
                      "red_flags": [], "empfehlung": "ANPASSEN", "empfehlung_begruendung": ""}

    score = match_json.get('ats_score', 0)
    empf  = match_json.get('empfehlung', 'ANPASSEN')
    print(f"     ATS Score: {score}/100 | Empfehlung: {empf}")

    if score < 30 and args.mode != "dry-run":
        print(f"\n  [SKIP] Score zu niedrig ({score}/100). Bewerbung nicht empfohlen.")
        print(f"  Fehlende Pflicht-Keywords: {match_json.get('tier1_fehlend', [])}")
        sys.exit(0)

    # STEP 3 — Lebenslauf
    print("\n[4/5] STEP 3 — Lebenslauf adaptieren...")
    if args.mode == "dry-run":
        lebenslauf_text = lebenslauf_master + "\n\n*[DRY-RUN: Keine Anpassung]*"
    else:
        lebenslauf_text = llm(build_lebenslauf_prompt(vacancy_json, match_json, lebenslauf_master))
    print("     OK")

    # STEP 4 — Anschreiben
    print("\n[4/5] STEP 4 — Anschreiben erstellen...")
    if args.mode == "dry-run":
        anschreiben_text = f"# Anschreiben [DRY-RUN]\n\n**Stelle:** {vacancy_json.get('stelle')}\n"
    else:
        anschreiben_text = llm(build_anschreiben_prompt(vacancy_json, match_json, kandidat_profil))
    print("     OK")

    # STEP 5 — Speichern
    print("\n[5/5] STEP 5 — Output speichern...")
    out_dir = save_output_package(vacancy_json, match_json, lebenslauf_text, anschreiben_text)
    log_to_db(vacancy_json, match_json, out_dir)

    print("\n" + "=" * 60)
    print(f"  FERTIG! Paket gespeichert in:")
    print(f"  {out_dir.relative_to(BASE_DIR)}")
    print(f"  ATS Score: {score}/100 | {empf}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
