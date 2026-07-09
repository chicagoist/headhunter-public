# 📂 DATABASE — Struktur & Inhalt
## HeadHunter PROJECT_beta | Stand: 08.07.2026

---

## Verzeichnisstruktur

```
DATABASE/
│
├── 00_CANDIDATE_PROFILE/           ← KANDIDATENDATEN (Quelle für den Agenten)
│   ├── kandidat_profil.md          Master-Profil: YAML + vollständige Daten
│   └── lebenslauf_master.md        ATS-bereiter Lebenslauf (MD, KEINE cite-Tags)
│
├── 01_STANDARDS/                   ← NORMEN & COMPLIANCE
│   ├── EU_AI_Act_HR_Compliance.md  High-Risk ATS, Rechte des Bewerbers
│   └── DIN_ISO_TUV_Standards.md    DIN SPEC 91426, ISO 10667, prEN 18286
│
├── 02_ATS_SYSTEMS/                 ← ATS-SYSTEMWISSEN
│   ├── ATS_Map_Germany_2026.md     Welche Firmen nutzen welches ATS
│   └── Keyword_Matrix_Java_AI.md   Keyword-Cluster für Java/AI-Profile
│
├── 03_TEMPLATES/                   ← VORLAGEN & PROMPTS
│   ├── Lebenslauf_Template_ATS.md  Formatierungsregeln + Strukturvorlage
│   ├── Anschreiben_Templates.md    3 Vorlagen + Timing-Strategie
│   └── Prompt_Library.md           8 AI-Prompts für verschiedene Aufgaben
│
├── 04_AUTOMATION/                  ← PYTHON-SKRIPTE
│   ├── agent.py                    ★ HAUPTSKRIPT — Vollautomatischer Agent v2.0
│   ├── setup_ats_db.py             Datenbank-Initialisierung
│   ├── cv_optimizer_prompt.py      Einzelner CV-Optimierungshelfer
│   └── Python_Automation_Stack.md  Tech-Stack-Dokumentation
│
├── 05_DATABASE/                    ← SQLITE-DATENBANK
│   ├── ats_optimization.db         Aktive Datenbank (30 Skills, 10 ATS-Patterns)
│   └── schema_description.md       ERD + SQL-Abfragen
│
├── 06_SKILLS/                      ← MARKT-ANALYSE
│   └── Skills_Map_2026.md          Nachfrage, Gehälter, Karrierewege
│
├── 07_TRAINING_DOCS/               ← TRAININGSMATERIAL (Zukunftsmotor)
│   ├── Checklist Anschreiben IT.odt    Checkliste Anschreiben (DIN 5008)
│   ├── KI Support Anschreiben IT.odt   KI-Feedback-Prompt für Anschreiben
│   ├── Interviewtraining.pdf           Interview-Vorbereitung
│   └── K22_Lebenslauf_Training.pdf     Lebenslauf-Training
│
└── README_STRUKTUR.md              ← DIESE DATEI
```

---

## Schnellstart — Agent starten

```powershell
# 1. Stellenanzeige als TXT speichern, z.B.:
#    DATABASE/04_AUTOMATION/test_vacancy.txt

# 2. Agent starten (dry-run, ohne LLM):
python DATABASE\04_AUTOMATION\agent.py --vacancy meine_vakanz.txt --mode dry-run

# 3. Agent mit lokalem Ollama (DeepSeek):
ollama serve                                      # Terminal 1
ollama pull deepseek-r1:7b                        # einmalig
python DATABASE\04_AUTOMATION\agent.py --vacancy meine_vakanz.txt --mode ollama

# 4. Ergebnisse finden in:
#    OUTPUT\Bewerbungen\[DATUM]_[FIRMA]_[STELLE]\
```

---

## Dateien, die NICHT verändert werden sollten

| Datei | Grund |
|---|---|
| `00_CANDIDATE_PROFILE/kandidat_profil.md` | Stammdaten — nur bei echten Änderungen |
| `00_CANDIDATE_PROFILE/lebenslauf_master.md` | Vorlage für den Agenten — sauber halten |
| `05_DATABASE/ats_optimization.db` | Von Python-Skript verwaltet |

---

## Datei-Versionierung

Bei größeren Änderungen (z.B. neues Zertifikat, neue Stelle):
1. `lebenslauf_master.md` aktualisieren
2. `kandidat_profil.md` → YAML-Block anpassen
3. Git-Commit: `git commit -m "CV Update: AZ-900 erhalten 07/2026"`
