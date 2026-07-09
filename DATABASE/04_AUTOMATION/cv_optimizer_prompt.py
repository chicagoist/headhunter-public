"""
HeadHunter CV Optimizer — AI-агент адаптации резюме
Использует локальный LLM через Ollama или API для оптимизации CV под конкретную вакансию.

Запуск: python cv_optimizer_prompt.py

Режимы:
  --mode ollama   → локальный DeepSeek через Ollama (приватно, бесплатно)
  --mode api      → OpenAI/Anthropic API (быстрее, платно)
  --mode analyze  → только анализ без генерации

Автор: HeadHunter PROJECT_beta
Версия: 2026.07
"""

import argparse
import json
import sys
import sqlite3
import os
from datetime import datetime

# Проверка зависимостей
try:
    import httpx
except ImportError:
    print("❌ httpx не установлен. Запустите: pip install httpx")
    sys.exit(1)

# ─── КОНФИГУРАЦИЯ ──────────────────────────────────────────────────────────────

CONFIG = {
    'ollama_base_url': 'http://localhost:11434',
    'ollama_model': 'deepseek-r1:latest',     # или 'deepseek-coder:latest'
    'db_path': os.path.join(os.path.dirname(__file__), '..', '05_DATABASE', 'ats_optimization.db'),
    'output_dir': os.path.join(os.path.dirname(__file__), '..', 'output'),
}

# ─── СИСТЕМНЫЙ ПРОМПТ ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Du bist ein erfahrener deutscher IT-Recruiter mit 10 Jahren Erfahrung 
auf dem deutschen Arbeitsmarkt (2026). Du kennst:
- ATS-Systeme (Workday, Personio, SAP SuccessFactors, Greenhouse, Lever)
- Deutsche CV-Standards (DIN SPEC 91426, ISO 10667)
- EU AI Act Anforderungen für HR-Systeme
- Aktuelle Tech-Trends (Java 21, Spring Boot 3, Spring AI, KI-Architektur)

Deine Bewertungen sind konkret, präzise und umsetzbar.
Antworte auf RUSSISCH (für den Kandidaten), außer wenn explizit Deutsch verlangt wird.
Ausgabe immer als strukturiertes JSON wenn nicht anders angegeben."""

# ─── ОСНОВНЫЕ ПРОМПТЫ ──────────────────────────────────────────────────────────

def build_analysis_prompt(cv_text: str, job_description: str) -> str:
    return f"""AUFGABE: Führe eine vollständige ATS-Gap-Analyse durch.

LEBENSLAUF:
---
{cv_text}
---

STELLENANZEIGE:
---
{job_description}
---

Analysiere und antworte NUR als JSON in diesem Format:
{{
  "ats_score": 0-100,
  "keyword_match": {{
    "tier1_present": ["список Tier1 ключевых слов которые ЕСТЬ"],
    "tier1_missing": ["список Tier1 ключевых слов которых НЕТ"],
    "tier2_present": ["список Tier2 ключевых слов которые ЕСТЬ"],
    "tier2_missing": ["список Tier2 ключевых слов которых НЕТ"],
    "tier1_pct": 0-100,
    "tier2_pct": 0-100
  }},
  "red_flags": [
    {{"issue": "описание проблемы", "severity": "HIGH/MEDIUM/LOW", "fix": "как исправить"}}
  ],
  "strengths": ["топ 3 сильные стороны для этой вакансии"],
  "recommended_bullets": [
    {{"original": "оригинальная строка из CV", "improved": "улучшенный вариант по формуле Action+Tech+Result+Metric"}}
  ],
  "anschreiben_hook": "первый абзац сопроводительного письма (2-3 предложения на немецком)",
  "overall_recommendation": "ПРИМЕНИТЬ_СЕЙЧАС | УЛУЧШИТЬ_СНАЧАЛА | НЕ_ПОДХОДИТ",
  "priority_actions": ["action 1", "action 2", "action 3"]
}}"""


def build_rewrite_prompt(cv_text: str, job_description: str, missing_keywords: list) -> str:
    keywords_str = ', '.join(missing_keywords)
    return f"""AUFGABE: Optimiere den Lebenslauf für diese Stellenanzeige.

LEBENSLAUF (Original):
---
{cv_text}
---

STELLENANZEIGE:
---
{job_description}
---

FEHLENDE KEYWORDS (müssen integriert werden):
{keywords_str}

REGELN:
1. Ändere KEINE Fakten - nur Formulierungen
2. Formel für jeden Bullet: [Aktionsverb] + [Technologie] + [Ergebnis] + [Metrik]
3. Integriere fehlende Keywords ORGANISCH in Kontext
4. Behalte deutschen Stil bei (falls Stellenanzeige auf Deutsch)
5. Human-in-the-Loop: Text soll wie von einem Menschen geschrieben wirken

Antworte als JSON:
{{
  "optimized_berufserfahrung": "полный переписанный раздел Berufserfahrung",
  "optimized_kenntnisse": "переписанный раздел Kenntnisse/Skills",
  "optimized_profil": "3-строчный профессиональный профиль",
  "changes_made": ["список изменений для контроля Human-in-the-Loop"],
  "keywords_integrated": ["список интегрированных ключевых слов"]
}}"""


# ─── OLLAMA ИНТЕГРАЦИЯ ─────────────────────────────────────────────────────────

def call_ollama(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """Вызов локального Ollama LLM"""
    try:
        response = httpx.post(
            f"{CONFIG['ollama_base_url']}/api/chat",
            json={
                "model": CONFIG['ollama_model'],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,     # Низкая температура = более предсказуемый вывод
                    "top_p": 0.9,
                }
            },
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()['message']['content']
    except httpx.ConnectError:
        print("❌ Ollama не запущен. Запустите: ollama serve")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка Ollama: {e}")
        sys.exit(1)


# ─── БАЗА ДАННЫХ ───────────────────────────────────────────────────────────────

def save_analysis_to_db(vacancy_data: dict, analysis_result: dict) -> int:
    """Сохранить результаты анализа в SQLite БД"""
    if not os.path.exists(CONFIG['db_path']):
        print("⚠️ БД не найдена. Запустите сначала setup_ats_db.py")
        return -1
    
    conn = sqlite3.connect(CONFIG['db_path'])
    cursor = conn.cursor()
    
    # Добавить компанию если нет
    cursor.execute(
        "INSERT OR IGNORE INTO companies (name, ats_system) VALUES (?, ?)",
        (vacancy_data.get('company', 'Unknown'), vacancy_data.get('ats_system', 'Unknown'))
    )
    company_id = cursor.execute(
        "SELECT company_id FROM companies WHERE name = ?", 
        (vacancy_data.get('company', 'Unknown'),)
    ).fetchone()[0]
    
    # Добавить вакансию
    cursor.execute(
        """INSERT INTO vacancies (company_id, job_title, job_url, source_platform, 
           job_description, date_found)
           VALUES (?, ?, ?, ?, ?, date('now'))""",
        (company_id, vacancy_data.get('title', ''), vacancy_data.get('url', ''),
         vacancy_data.get('platform', ''), vacancy_data.get('description', ''))
    )
    vacancy_id = cursor.lastrowid
    
    # Добавить итерацию CV
    cursor.execute(
        """INSERT INTO cv_iterations (vacancy_id, ats_score, keyword_match_pct,
           ai_tools_used, notes, human_reviewed)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (vacancy_id, 
         analysis_result.get('ats_score', 0),
         analysis_result.get('keyword_match', {}).get('tier1_pct', 0),
         CONFIG['ollama_model'],
         json.dumps(analysis_result.get('priority_actions', []), ensure_ascii=False))
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ Данные сохранены в БД. Vacancy ID: {vacancy_id}")
    return vacancy_id


# ─── ГЛАВНАЯ ФУНКЦИЯ ───────────────────────────────────────────────────────────

def analyze_vacancy(cv_text: str, job_description: str, save_db: bool = True):
    """Анализ вакансии и CV"""
    print(f"\n🔍 Анализ начат: {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Модель: {CONFIG['ollama_model']}")
    
    prompt = build_analysis_prompt(cv_text, job_description)
    
    print("   Отправка запроса к LLM...")
    raw_response = call_ollama(prompt)
    
    # Извлечь JSON из ответа
    try:
        # Попытка найти JSON в ответе
        start = raw_response.find('{')
        end = raw_response.rfind('}') + 1
        json_str = raw_response[start:end]
        result = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        print("⚠️ Не удалось распарсить JSON. Сырой ответ:")
        print(raw_response)
        return None
    
    # Вывод результата
    print(f"\n{'='*60}")
    print(f"📊 ATS SCORE: {result.get('ats_score', 'N/A')}/100")
    print(f"{'='*60}")
    
    kw = result.get('keyword_match', {})
    print(f"\n🔑 KEYWORD MATCHING:")
    print(f"   Tier 1 (Must Have): {kw.get('tier1_pct', 0):.0f}%")
    print(f"   Tier 2 (Important): {kw.get('tier2_pct', 0):.0f}%")
    
    if kw.get('tier1_missing'):
        print(f"\n❌ ОТСУТСТВУЮТ Tier 1 keywords:")
        for kw_missing in kw['tier1_missing']:
            print(f"   • {kw_missing}")
    
    if result.get('red_flags'):
        print(f"\n⚠️ RED FLAGS:")
        for flag in result['red_flags']:
            severity_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(flag.get('severity', ''), '⚪')
            print(f"   {severity_icon} {flag.get('issue', '')}")
            print(f"      Fix: {flag.get('fix', '')}")
    
    print(f"\n✅ СИЛЬНЫЕ СТОРОНЫ:")
    for strength in result.get('strengths', []):
        print(f"   • {strength}")
    
    print(f"\n🎯 РЕКОМЕНДАЦИЯ: {result.get('overall_recommendation', 'N/A')}")
    
    print(f"\n📋 ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ:")
    for i, action in enumerate(result.get('priority_actions', []), 1):
        print(f"   {i}. {action}")
    
    if result.get('anschreiben_hook'):
        print(f"\n✉️ HOOK ДЛЯ ANSCHREIBEN:")
        print(f"   {result['anschreiben_hook']}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description='HeadHunter CV Optimizer')
    parser.add_argument('--cv', type=str, help='Путь к файлу CV (txt)')
    parser.add_argument('--job', type=str, help='Путь к файлу вакансии (txt)')
    parser.add_argument('--mode', choices=['analyze', 'rewrite', 'full'], 
                        default='analyze', help='Режим работы')
    args = parser.parse_args()
    
    print("🚀 HeadHunter CV Optimizer v2026.07")
    print("=" * 60)
    
    # Тестовый режим без файлов
    if not args.cv and not args.job:
        print("ℹ️ Режим демонстрации (без файлов)")
        print("   Используйте: --cv [путь_к_cv.txt] --job [путь_к_вакансии.txt]")
        print("\n   Пример:")
        print("   python cv_optimizer_prompt.py --cv my_cv.txt --job vacancy.txt --mode full")
        return
    
    cv_text = open(args.cv, encoding='utf-8').read() if args.cv else ""
    job_text = open(args.job, encoding='utf-8').read() if args.job else ""
    
    if args.mode in ['analyze', 'full']:
        result = analyze_vacancy(cv_text, job_text)
    
    if args.mode == 'rewrite' and result:
        missing = result.get('keyword_match', {}).get('tier1_missing', [])
        print(f"\n📝 Переписываю CV с интеграцией {len(missing)} keywords...")
        rewrite_prompt = build_rewrite_prompt(cv_text, job_text, missing)
        rewrite_result = call_ollama(rewrite_prompt)
        print("\n" + "="*60)
        print("ОПТИМИЗИРОВАННЫЕ СЕКЦИИ CV:")
        print(rewrite_result)


if __name__ == '__main__':
    main()
