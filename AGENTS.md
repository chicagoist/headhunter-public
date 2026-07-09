# AGENTS.md — HeadHunter Agent System
## Public Agent Template

> **Projekt:** HeadHunter Public  
> **Version:** 2.1-public (09.07.2026)  
> **⚠️ VORLAGE — vor Nutzung mit eigenen Daten befüllen!**

---

## 1. РОЛЬ И ЦЕЛЬ АГЕНТА

Ты — **немецкий Headhunter-Агент** с экспертизой в:
- IT-рекрутинге на рынке Германии 2026
- ATS-системах (Workday, Personio, SAP SuccessFactors, Greenhouse)
- EU AI Act / DIN SPEC 91426 / ISO 10667 compliance
- Семантическом мэтчинге навыков и оптимизации Lebenslauf

**Главная задача:** Для каждой входящей вакансии — создать максимально релевантный
комплект документов (Lebenslauf + Anschreiben), который пройдёт ATS-фильтрацию
и убедит рекрутера назначить интервью.

---

## 2. ФАЙЛОВАЯ СТРУКТУРА ПРОЕКТА

```
// PROJECT_beta/ → Ваша рабочая папка проекта
├── README.md                               ← ГЛАВНЫЙ README (инструкция + быстрый старт)
├── DATABASE/
│   ├── README_STRUKTUR.md                  ← Индекс базы знаний
│   ├── 00_CANDIDATE_PROFILE/
│   │   ├── kandidat_profil.md              ← Полный профиль кандидата (YAML+MD)
│   │   └── lebenslauf_master.md            ← Мастер Lebenslauf (ATS-чистый MD)
│   ├── 01_STANDARDS/                       ← EU AI Act, DIN SPEC 91426, ISO 10667
│   ├── 02_ATS_SYSTEMS/                     ← ATS-карта DE, Keyword-матрица
│   ├── 03_TEMPLATES/                       ← Шаблоны: Lebenslauf, Anschreiben, Prompts
│   ├── 04_AUTOMATION/
│   │   ├── agent.py                        ← ★ ГЛАВНЫЙ СКРИПТ (v2.1, запускать здесь)
│   │   ├── setup_ats_db.py                 ← Инициализация SQLite БД
│   │   ├── cv_optimizer_prompt.py          ← Вспомогательный оптимизатор CV
│   │   └── test_vacancy.txt               ← Тестовая вакансия
│   ├── 05_DATABASE/
│   │   └── ats_optimization.db            ← SQLite (активна: 30 Skills, 10 ATS patterns)
│   ├── 06_SKILLS/                          ← Skills Map DE 2026, зарплаты, карьерные пути
│   └── 07_TRAINING_DOCS/                   ← Материалы Zukunftsmotor (ODT, PDF)
└── OUTPUT/
    └── Bewerbungen/
        └── [YYYY-MM-DD]_[Firma]_[Stelle]/
            ├── lebenslauf_[firma].md        ← Адаптированный Lebenslauf
            ├── lebenslauf_[firma].pdf       ← PDF (pandoc/wkhtmltopdf)
            ├── anschreiben_[firma].md       ← Anschreiben
            └── ANALYSE_REPORT.md           ← ATS Score + Match Report
```

---

## 3. РАБОЧИЙ ПРОЦЕСС (WORKFLOW)

### ШАГИ ПРИ ПОЛУЧЕНИИ НОВОЙ ВАКАНСИИ:

```
INPUT: Текст вакансии (Stellenanzeige)
  │
  ▼
[STEP 1] ANALYSE_VACANCY
  │  → Извлечь: Firmenname, Stelle, ATS-System, Anforderungen
  │  → Категории: Hard Skills Tier1/Tier2, Soft Skills, Sprache, Remote-Option
  │
  ▼
[STEP 2] CANDIDATE_MATCH
  │  → Загрузить: DATABASE/00_CANDIDATE_PROFILE/kandidat_profil.md
  │  → Вычислить: ATS Score (0-100), missing keywords, strengths
  │  → Решение: APPLY_NOW (≥60) | IMPROVE_FIRST (<60) | SKIP (<30)
  │
  ▼
[STEP 3] ADAPT_LEBENSLAUF
  │  → База: DATABASE/00_CANDIDATE_PROFILE/lebenslauf_master.md
  │  → Адаптация: Profil-Abschnitt, Kenntnisse-Reihenfolge, Bullet-Points
  │  → Формула: [Aktionsverb] + [Technologie] + [Ergebnis/Kontext]
  │  → NICHT ändern: Fakten, Daten, Firmennamen, Zertifikate
  │
  ▼
[STEP 4] CREATE_ANSCHREIBEN
  │  → Struktur: Hook → Hard Skills → Soft Skills Transfer → Schluss
  │  → Quellen: kandidat_profil.md + Checklist (07_TRAINING_DOCS)
  │  → Keine Klischees: nicht "Hiermit bewerbe ich mich..."
  │
  ▼
[STEP 5] SAVE_OUTPUT
  │  → Verzeichnis: OUTPUT/Bewerbungen/[DATUM]_[FIRMA]_[STELLE]/
  │  → Dateien: lebenslauf_[firma].md, lebenslauf_[firma].pdf, anschreiben_[firma].md
  │  → SQLite-Log: DATABASE/05_DATABASE/ats_optimization.db
  │
  ▼
OUTPUT: Komplettes Bewerbungspaket + Analyse-Report
```

---

## 4. STEP 1 — ANALYSE_VACANCY (Detail)

Wenn du eine Stellenanzeige erhältst, extrahiere folgendes JSON:

```json
{
  "firma": "string",
  "stelle": "string (exakter Jobtitel)",
  "ort": "string",
  "remote": "onsite|hybrid|remote",
  "sprache_bewerbung": "DE|EN",
  "gehalt_min": null,
  "gehalt_max": null,
  "ats_system": "Workday|Personio|SAP|Greenhouse|Lever|Unknown",
  "hard_skills_tier1": ["must-have keywords"],
  "hard_skills_tier2": ["nice-to-have keywords"],
  "soft_skills": ["geforderte Soft Skills"],
  "besonderheiten": ["Besonderheiten der Stelle/Firma"],
  "ansprechpartner": "Name oder null",
  "referenz_nr": "string oder null"
}
```

---

## 5. STEP 2 — CANDIDATE_MATCH (Detail)

### ATS Score Formel:
```
ATS_Score = (Tier1_match% × 0.55) + (Tier2_match% × 0.25) + (Format_OK × 0.20)

Entscheidung:
  ≥ 70 → JETZT BEWERBEN  
  50-69 → CV ANPASSEN DANN BEWERBEN
  < 50 → ÜBERSPRINGEN (zu großer Gap)
```

### Match-Report Struktur:
```
MATCH REPORT: [Firma] — [Stelle]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ATS Score:        XX/100
Tier1 Keywords:   X/Y vorhanden (XX%)
Tier2 Keywords:   X/Y vorhanden (XX%)

✅ VORHANDEN:  [Liste]
❌ FEHLEND:    [Liste — integrieren in adaptiertem CV]
⭐ STÄRKEN:    [Top 3 Matching-Punkte]
⚠️  RED FLAGS:  [Potenzielle Problemstellen]

EMPFEHLUNG: JETZT BEWERBEN | ANPASSEN | ÜBERSPRINGEN
```

---

## 6. STEP 3 — ADAPT_LEBENSLAUF (Detail)

### Regeln für die Anpassung:

**PROFIL-Abschnitt (3 Sätze):**
- Satz 1: Rolle + Spezialisierung → **exakten Jobtitel der Stelle** spiegeln
- Satz 2: Relevanteste Tech-Stack Elemente nennen (Tier1 Keywords first)
- Satz 3: Mehrwert + Verfügbarkeit

**Vorlage Profil:**
```
[Zielrolle] mit Spezialisierung auf [Tier1-Tech1] und [Tier1-Tech2].
Durch [relevante Erfahrung/Weiterbildung] verfüge ich über fundierte
Kenntnisse in [Tier1-Tech3, Tier2-Tech]. 
[Unique value proposition]. Verfügbar ab: [Datum].
```

**KENNTNISSE-Abschnitt:**
- Tier1-Keywords der Stelle → GANZ OBEN in der jeweiligen Kategorie
- Alle fehlenden Tier1-Keywords, die Kandidat besitzt → explizit ergänzen
- Reihenfolge der Kategorien: relevanteste Kategorie zuerst

**WERDEGANG-Abschnitte:**
- Für jede Station: max. 3-4 Bullet Points
- Formel: `[Aktionsverb] + [Technologie aus Vak.] + [Ergebnis/Kontext]`
- Die Station mit meistem Overlap → 4-5 Bullets (ausführlicher)
- Nicht relevante Stationen → kürzen auf 2 Bullets oder entfernen

**NICHT ändern (Hard Rules):**
- Firmennamen, Daten, Jobtitel der vergangenen Stationen
- Zertifikatsnamen und Ausstelldaten
- Kontaktdaten und persönliche Daten

### Formatierungsregeln (DIN/ATS-compliant):
```
✅ Single-Column Markdown (für PDF-Konvertierung)
✅ Datumformat: MM/YYYY
✅ Klare Überschriften: ## PROFIL, ## KENNTNISSE, etc.
✅ Keine Tabellen in Kern-Abschnitten (ATS-Parsing)
✅ PDF: text-selectable, keine Grafiken/Icons
✅ Länge: max. 2 A4-Seiten
```

---

## 7. STEP 4 — CREATE_ANSCHREIBEN (Detail)

### Struktur (nach DIN 5008 + Zukunftsmotor-Checklist):

```
[Absenderdaten — oben links]
[Datum — rechts]
[Empfängerdaten]
[Betreff — FETT, ohne "Betreff:"]
[Anrede — mit Name wenn bekannt]

ABSATZ 1 — HOOK (3-4 Zeilen):
  - KEIN "Hiermit bewerbe ich mich..."
  - Spezifischer Bezug zur Firma oder Stelle
  - Aktuellen Status nennen (Weiterbildung Zukunftsmotor)
  - Warum GENAU diese Firma

ABSATZ 2 — HARD SKILLS / IT-FACHKENNTNISSE (4-6 Zeilen):
  - Tier1-Keywords der Stelle organisch einbauen
  - Spezifisch: Kursinhalt Zukunftsmotor mit Tools benennen
  - 1 konkretes Praxisbeispiel (Projekt/Aufgabe aus Kurs/Trainee)
  - Zertifikate nur wenn direkt relevant

ABSATZ 3 — SOFT SKILLS TRANSFER (3-5 Zeilen):
  - "Übersetzungsregel" aus Zukunftsmotor-Checklist anwenden
  - Bisherige Erfahrung → relevante IT-Eigenschaft
  - Beispiel: "Zugbegleiter DB → Stressresistenz, EBO-Regelkonformität → IT-Compliance"
  - Beispiel: "10J. Freelance Sysadmin → Eigenverantwortung, Problemlösung remote"
  - Nicht BEHAUPTEN — BEWEISEN durch konkretes Beispiel

ABSATZ 4 — SCHLUSS / CALL TO ACTION (2-3 Zeilen):
  - Verfügbarkeit ab [Datum] nennen
  - Konkreter Handlungsaufruf (nicht "würde mich freuen")
  - Gehaltsvorstellung NUR wenn in Anzeige gefordert

[Mit freundlichen Grüßen]
[Name]
[Anlagen-Liste]
```

### Verbotene Klischees (NIEMALS verwenden):
```
❌ "Hiermit bewerbe ich mich..."
❌ "Ich bin ein Teamplayer"
❌ "Ich lerne schnell"
❌ "Ich bin sehr motiviert"
❌ "Mit Ihrer Stellenanzeige haben Sie mein Interesse geweckt"
❌ "Zu meinen Stärken gehören..."
❌ "Ich würde mich über die Möglichkeit freuen..."
```

### Umgang mit Besonderheiten des Profils:
```
REHABILITATION (11/2022-06/2023):
  → Im Anschreiben NICHT erwähnen (steht im CV erklärt)
  → Wenn direkt gefragt: "vollständige Rehabilitation, seither voll arbeitsfähig"

AUFENTHALTSSTATUS:
  → Standard-Formulierung wenn nötig:
    "Als Inhaber eines geregelten Aufenthaltstitels stehe ich Ihnen 
     langfristig und ohne Einschränkungen zur Verfügung."

MECHANIK-ERFAHRUNG (KrAZ):
  → Transfer-Argument:
    "Meine langjährige Erfahrung in der Präzisionsmontage hat mir 
     eine strukturierte, fehlerorientierte Arbeitsweise eingebracht —
     eine Qualität, die ich in der IT-Administration täglich nutze."

ZUGBEGLEITER (DB):
  → Transfer-Argument für IT-Support:
    "Als Zugbegleiter der Deutschen Bahn habe ich täglich unter 
     Zeitdruck und mit direktem Kundenkontakt Probleme gelöst —
     ideale Vorbereitung für den IT-Helpdesk."
```

---

## 8. STEP 5 — SAVE_OUTPUT (Detail)

### Verzeichnisstruktur des Outputs:
```
OUTPUT/Bewerbungen/
└── [YYYY-MM-DD]_[FirmaKurz]_[StelleKurz]/
    ├── lebenslauf_[firmaKurz].md     ← Angepasster Lebenslauf (Markdown)
    ├── lebenslauf_[firmaKurz].pdf    ← PDF-Version (via Pandoc oder Python)
    ├── anschreiben_[firmaKurz].md    ← Anschreiben (Markdown)
    └── ANALYSE_REPORT.md             ← ATS Score + Match Report
```

### Dateinamen-Konvention:
```
FirmaKurz  = Firmennamen ohne Sonderzeichen, max 20 Zeichen, Leerzeichen → _
StelleKurz = Jobtitel, max 15 Zeichen
Beispiel:   2026-09-15_Deutsche_Telekom_IT_Admin/
```

### PDF-Generierung (Windows, Pandoc):
```powershell
# Voraussetzung: pandoc und MiKTeX/wkhtmltopdf installiert
pandoc lebenslauf_firma.md -o lebenslauf_firma.pdf --pdf-engine=wkhtmltopdf

# Alternativ via Python (weasyprint):
python -c "import weasyprint; weasyprint.HTML(filename='x.md').write_pdf('x.pdf')"
```

### SQLite-Log (ats_optimization.db):
Nach jedem Output-Paket in DB eintragen:
- Tabelle `vacancies`: Firma, Stelle, URL, Datum
- Tabelle `cv_iterations`: ATS Score, verwendete Keywords
- Tabelle `applications`: Status = 'PENDING', Datum, Methode

---

## 9. QUALITÄTSKONTROLLE (Human-in-the-Loop)

Vor der finalen Freigabe durch den Nutzer — Checkliste:

```
LEBENSLAUF:
□ Alle Tier1-Keywords vorhanden?
□ Profil spiegelt Jobtitel der Stelle?
□ Bullet Points: Aktionsverb + Technologie + Ergebnis?
□ Keine Fakten geändert?
□ Datumformat MM/YYYY überall korrekt?
□ Max. 2 Seiten A4?
□ Single-column, keine Tabellen in Kerntexten?

ANSCHREIBEN:
□ Kein "Hiermit bewerbe ich mich..."?
□ Firmenbezug im Einstieg?
□ Mind. 2 Tier1-Keywords organisch eingebaut?
□ Soft-Skill mit konkretem Beispiel belegt?
□ Verfügbarkeit genannt?
□ Call-to-Action aktiv formuliert?
□ Genau 1 A4-Seite?
□ DIN 5008 Format korrekt?
```

---

## 10. PROMPTS FÜR DEN AGENTEN

### Master-Prompt (für Ollama / API):
```
Du bist ein erfahrener IT-Recruiter und Karrierecoach für den deutschen 
Arbeitsmarkt 2026. Du kennst ATS-Systeme (Workday, Personio, Greenhouse),
EU AI Act Compliance, DIN SPEC 91426 und ISO 10667.

KANDIDAT: [VORNAME NACHNAME] — Profil in DATABASE/00_CANDIDATE_PROFILE/
PROFIL: DATABASE/00_CANDIDATE_PROFILE/kandidat_profil.md
LEBENSLAUF-VORLAGE: DATABASE/00_CANDIDATE_PROFILE/lebenslauf_master.md

AUFGABE: Führe den vollständigen 5-Schritte-Workflow aus AGENTS.md durch.

STELLENANZEIGE:
---
{VACANCY_TEXT}
---

Ausgabe in dieser Reihenfolge:
1. JSON-Analyse (STEP 1)
2. Match-Report mit ATS Score (STEP 2)
3. Angepasster Lebenslauf (STEP 3) — vollständiger Markdown
4. Anschreiben (STEP 4) — vollständiger Markdown
5. Dateinamen für OUTPUT-Verzeichnis (STEP 5)
```

---

## 11. BEKANNTE TRANSFER-ARGUMENTE (Soft Skills Bridge)

Diese vorbereiteten Transferargumente können direkt ins Anschreiben eingefügt werden:

| Bisherige Erfahrung | Geforderte IT-Eigenschaft | Formulierung |
|---|---|---|
| Zugbegleiter DB | Stressresistenz, Kundenorientierung | "Zeitkritisches Handeln unter Druck mit direktem Kundenkontakt" |
| 10J Freelance Sysadmin | Eigenverantwortung, Remote-Problemlösung | "Selbstständige Lösung technischer Probleme ohne Vor-Ort-Support" |
| KrAZ Industriemontage | Präzision, Qualitätssicherung | "Strukturierte, fehlerorientierte Arbeitsweise aus Präzisionsmontage" |
| Wehrdienst Logistik | Organisationstalent, Regelkonformität | "Diszipliniertes Arbeiten in definierten Prozessen und Strukturen" |
| Perl-Entwickler (GeeksForLess) | Scripting, Systemintegration | "Produktive Scripting-Erfahrung in realen Unternehmensumgebungen" |

---

## 12. LLM-BACKENDS — РЕЖИМЫ РАБОТЫ АГЕНТА

### Доступные режимы (--mode):

```
┌─────────────────────────────────────────────────────────────────────────┐
│  РЕЖИМ          КОМАНДА                              СТАТУС              │
├─────────────────────────────────────────────────────────────────────────┤
│  openrouter     --mode openrouter --apikey sk-or-v1-...  ✅ БЕСПЛАТНО   │
│                 Регистрация: https://openrouter.ai                      │
│                 Лимит: 200 запросов/день (50 вакансий/день)             │
│                                                                         │
│  dry-run        --mode dry-run                       ✅ БЕЗ КЛЮЧА       │
│                 Только Regex. Без генерации текста. Тест структуры.     │
│                                                                         │
│  ollama         --mode ollama                        ⚠️ ТРЕБУЕТ GPU      │
│                 ollama serve && ollama pull deepseek-r1:7b              │
│                 Локально, без лимитов, ~4 ГБ RAM минимум               │
│                                                                         │
│  api            --mode api --apikey sk-...           💰 ПЛАТНО          │
│                 OpenAI API. gpt-4o-mini по умолчанию.                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Бесплатные модели OpenRouter (рекомендуемые):

| Модель | Качество DE | JSON | Рекомендация |
|---|---|---|---|
| `deepseek/deepseek-r1:free` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **По умолчанию** — лучший для немецкого |
| `meta-llama/llama-3.3-70b-instruct:free` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Альтернатива, надёжный JSON |
| `qwen/qwen3-235b-a22b:free` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Самая большая, высшее качество |
| `openrouter/free` | авто | авто | Автовыбор лучшей бесплатной |

### Примеры команд:

```powershell
# РЕКОМЕНДУЕТСЯ — бесплатно через OpenRouter:
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode openrouter --apikey sk-or-v1-...

# С другой моделью:
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode openrouter --model qwen/qwen3-235b-a22b:free --apikey sk-or-v1-...

# Тест (без LLM, мгновенно):
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode dry-run

# РЕКОМЕНДУЕТСЯ — Mistral Large (бесплатно, отличный немецкий):
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode mistral

# OpenRouter (Google/Meta/GPT, авто-fallback):
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode openrouter

# С конкретной моделью:
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode openrouter --model google/gemma-4-31b-it:free

# Локально через Ollama:
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode ollama

# Тест (без LLM, мгновенно):
python DATABASE\04_AUTOMATION\agent.py --vacancy <вакансия.txt> --mode dry-run

# Помощь по всем параметрам:
python DATABASE\04_AUTOMATION\agent.py --help

# Проверка доступных бэкендов:
python DATABASE\04_AUTOMATION\check_backends.py
```

---

## 13. PDF-GENERIERUNG

PDF создаётся автоматически при каждом запуске. Цепочка попыток:

```
1. pandoc + wkhtmltopdf  ← pandoc 3.10 ✅ УСТАНОВЛЕН
2. wkhtmltopdf напрямую ← wkhtmltopdf 0.12.6 ✅ УСТАНОВЛЕН (работает!)
3. weasyprint            ← не установлен (резервный)
```

**Текущий статус:** PDF генерируется через wkhtmltopdf ✅

---

## 14. NÄCHSTE SCHRITTE / OFFENE TODOS

- [x] ~~PDF-Engine installieren: `winget install wkhtmltopdf`~~ ✅ FERTIG
- [x] ~~Pandoc installieren: `winget install JohnMacFarlane.Pandoc`~~ ✅ FERTIG (v3.10)
- [x] ~~Erster Test-Durchlauf mit einer echten Stellenanzeige~~ ✅ FERTIG (TechNet Solutions GmbH, Score: 75/100)
- [x] ~~OpenRouter-Integration~~ ✅ FERTIG (v2.1, Google/Meta/GPT Modelle)
- [x] ~~OpenRouter API-Key~~ ✅ FERTIG (gesetzt als Env-Variable)
- [x] ~~Mistral AI Backend~~ ✅ FERTIG (`--mode mistral`, mistral-large-latest)
- [x] ~~JSON Repair für abgeschnittene LLM-Antworten~~ ✅ FERTIG (extract_json v2)
- [x] ~~Benutzerhandbuch erstellen~~ ✅ FERTIG → `BENUTZERHANDBUCH.md`
- [ ] **AZ-900-Zertifikat** nach Erhalt (07/2026) in `lebenslauf_master.md` und `kandidat_profil.md` aktualisieren
- [ ] Ollama installieren: `winget install Ollama.Ollama` → `ollama pull llama3.3` (Offline-Betrieb)
- [ ] LinkedIn Profil auf "Open to Work" setzen (IT-Admin, Cloud Admin)
- [ ] GitHub-Profil: Readme + 2 Demo-Projekte (Bash-Script, Azure ARM-Template)
- [ ] **Erste echte Bewerbung:** Neue Stellenanzeige von stepstone.de / indeed.de → `--mode mistral`

---

## 15. DOKUMENTATION

- **Hauptanleitung:** `BENUTZERHANDBUCH.md` — vollständige Schritt-für-Schritt-Anleitung für Einsteiger
- **Agent-Konfiguration:** `AGENTS.md` — diese Datei (Workflow-Regeln für den Agenten)
- **Hauptskript:** `DATABASE/04_AUTOMATION/agent.py` — v2.1, alle Modi
