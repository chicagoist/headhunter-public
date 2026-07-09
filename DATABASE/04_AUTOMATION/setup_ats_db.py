"""
HeadHunter ATS Optimization Database
Скрипт инициализации SQLite базы данных для отслеживания откликов на вакансии.

Запуск: python setup_ats_db.py
Расположение БД: DATABASE/05_DATABASE/ats_optimization.db

Автор: HeadHunter PROJECT_beta
Версия: 2026.07
"""

import sqlite3
import os
import sys
import io
from datetime import datetime

# Установить UTF-8 для Windows консоли
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── КОНФИГУРАЦИЯ ──────────────────────────────────────────────────────────────
DB_DIR = os.path.join(os.path.dirname(__file__), '..', '05_DATABASE')
DB_PATH = os.path.join(DB_DIR, 'ats_optimization.db')

# ─── SQL СХЕМА ─────────────────────────────────────────────────────────────────
SCHEMA = """
-- ============================================================
-- ТАБЛИЦА 1: Компании
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    company_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    industry        TEXT,
    size            TEXT,           -- 'startup', 'SMB', 'Mittelstand', 'Konzern'
    website         TEXT,
    kununu_url      TEXT,
    kununu_score    REAL,           -- Рейтинг Kununu
    glassdoor_score REAL,
    ats_system      TEXT,           -- 'Workday', 'Personio', 'SAP SuccessFactors', etc.
    betriebsrat     INTEGER DEFAULT 0,  -- 1 = есть Betriebsrat
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- ТАБЛИЦА 2: Вакансии
-- ============================================================
CREATE TABLE IF NOT EXISTS vacancies (
    vacancy_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id          INTEGER NOT NULL,
    job_title           TEXT NOT NULL,
    job_url             TEXT,
    source_platform     TEXT,       -- 'LinkedIn', 'StepStone', 'XING', 'Indeed', 'Direct'
    location            TEXT,
    remote_option       TEXT,       -- 'onsite', 'hybrid', 'remote'
    salary_min          INTEGER,
    salary_max          INTEGER,
    required_skills     TEXT,       -- JSON или comma-separated
    required_language   TEXT,       -- 'DE', 'EN', 'DE+EN'
    job_description     TEXT,       -- Полный текст вакансии
    deadline_date       DATE,
    date_posted         DATE,
    date_found          DATE NOT NULL DEFAULT (date('now')),
    is_active           INTEGER DEFAULT 1,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- ============================================================
-- ТАБЛИЦА 3: Версии CV (итерации)
-- ============================================================
CREATE TABLE IF NOT EXISTS cv_iterations (
    iteration_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vacancy_id              INTEGER NOT NULL,
    cv_file_path            TEXT,           -- путь к файлу CV
    anschreiben_file_path   TEXT,           -- путь к Anschreiben
    ats_score               REAL,           -- Semantic match score (0-100)
    keyword_match_pct       REAL,           -- % совпадения ключевых слов
    din_spec_compliant      INTEGER DEFAULT 1,  -- Соответствие DIN SPEC 91426
    iso_10667_compliant     INTEGER DEFAULT 1,  -- Соответствие ISO 10667
    human_reviewed          INTEGER DEFAULT 1,  -- Human-in-the-loop check
    ai_tools_used           TEXT,           -- 'DeepSeek', 'GPT-4o', etc.
    notes                   TEXT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vacancy_id) REFERENCES vacancies(vacancy_id)
);

-- ============================================================
-- ТАБЛИЦА 4: Отклики и статусы
-- ============================================================
CREATE TABLE IF NOT EXISTS applications (
    application_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id        INTEGER NOT NULL,
    application_date    DATE NOT NULL DEFAULT (date('now')),
    application_method  TEXT,       -- 'Email', 'Portal', 'LinkedIn', 'Direct'
    status              TEXT DEFAULT 'PENDING',
    -- Статусы: PENDING | ATS_REVIEW | HR_REVIEW | PHONE_SCREEN |
    --          TECH_INTERVIEW | ASSESSMENT | FINAL_INTERVIEW |
    --          OFFER | REJECTED_AUTO | REJECTED_HR | REJECTED_INTERVIEW |
    --          WITHDRAWN | BLACKLISTED
    rejection_reason    TEXT,       -- Причина отказа (если известна)
    response_date       DATE,
    follow_up_date      DATE,       -- Когда отправить follow-up
    contact_person      TEXT,       -- Имя HR-менеджера
    contact_email       TEXT,
    feedback_notes      TEXT,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iteration_id) REFERENCES cv_iterations(iteration_id)
);

-- ============================================================
-- ТАБЛИЦА 5: Интервью
-- ============================================================
CREATE TABLE IF NOT EXISTS interviews (
    interview_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id      INTEGER NOT NULL,
    interview_date      DATETIME,
    interview_type      TEXT,   -- 'Phone', 'Video', 'Onsite', 'Technical', 'HR'
    round_number        INTEGER DEFAULT 1,
    interviewer_names   TEXT,
    questions_asked     TEXT,   -- Записи вопросов
    my_answers_notes    TEXT,
    outcome             TEXT,   -- 'PASS', 'FAIL', 'PENDING'
    feedback_received   TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(application_id)
);

-- ============================================================
-- ТАБЛИЦА 6: Навыки (Skills database)
-- ============================================================
CREATE TABLE IF NOT EXISTS skills (
    skill_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name      TEXT NOT NULL UNIQUE,
    category        TEXT,   -- 'Java', 'AI', 'Cloud', 'DevOps', 'DB', 'Soft'
    tier            INTEGER,    -- 1=Must Have, 2=Important, 3=Nice to Have
    market_demand   TEXT,   -- 'HIGH', 'MEDIUM', 'LOW'
    last_verified   DATE
);

-- ============================================================
-- ТАБЛИЦА 7: ATS паттерны (что работает)
-- ============================================================
CREATE TABLE IF NOT EXISTS ats_patterns (
    pattern_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ats_system      TEXT NOT NULL,
    pattern_type    TEXT,   -- 'keyword', 'format', 'structure', 'length'
    description     TEXT NOT NULL,
    effectiveness   INTEGER,    -- 1-10 рейтинг эффективности
    verified_date   DATE,
    source          TEXT    -- откуда информация
);

-- ============================================================
-- ИНДЕКСЫ для производительности
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_vacancies_company ON vacancies(company_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_date ON applications(application_date);
CREATE INDEX IF NOT EXISTS idx_cv_vacancy ON cv_iterations(vacancy_id);
"""

# ─── БАЗОВЫЕ ДАННЫЕ: Skills ────────────────────────────────────────────────────
INITIAL_SKILLS = [
    ('Java 21', 'Java', 1, 'HIGH'),
    ('Java 17', 'Java', 1, 'HIGH'),
    ('Spring Boot 3', 'Java', 1, 'HIGH'),
    ('Spring Framework', 'Java', 1, 'HIGH'),
    ('Spring MVC', 'Java', 1, 'HIGH'),
    ('Spring Security', 'Java', 1, 'HIGH'),
    ('Spring Data JPA', 'Java', 1, 'HIGH'),
    ('Spring AI', 'AI', 1, 'HIGH'),
    ('Microservices', 'Java', 1, 'HIGH'),
    ('REST API', 'Java', 1, 'HIGH'),
    ('Docker', 'DevOps', 1, 'HIGH'),
    ('Kubernetes', 'DevOps', 1, 'HIGH'),
    ('Git', 'DevOps', 1, 'HIGH'),
    ('CI/CD', 'DevOps', 1, 'HIGH'),
    ('PostgreSQL', 'DB', 1, 'HIGH'),
    ('JUnit 5', 'Java', 1, 'HIGH'),
    ('Azure (AZ-900)', 'Cloud', 2, 'HIGH'),
    ('GitHub Actions', 'DevOps', 2, 'MEDIUM'),
    ('Redis', 'DB', 2, 'MEDIUM'),
    ('Kafka', 'DB', 2, 'MEDIUM'),
    ('LangChain4j', 'AI', 2, 'HIGH'),
    ('RAG Architecture', 'AI', 2, 'HIGH'),
    ('LLM Integration', 'AI', 2, 'HIGH'),
    ('Prompt Engineering', 'AI', 2, 'HIGH'),
    ('ChromaDB', 'AI', 2, 'MEDIUM'),
    ('Ollama', 'AI', 2, 'MEDIUM'),
    ('Python 3', 'AI', 2, 'HIGH'),
    ('SQL', 'DB', 1, 'HIGH'),
    ('Agile/Scrum', 'Soft', 1, 'HIGH'),
    ('TDD', 'Java', 2, 'MEDIUM'),
]

# ─── ATS ПАТТЕРНЫ ──────────────────────────────────────────────────────────────
INITIAL_ATS_PATTERNS = [
    ('Workday', 'format', 'Single-column PDF обязателен, multi-column ломает parsing', 10, 'LinkedIn community'),
    ('Workday', 'keyword', 'Использует NLP — контекст важнее точного совпадения слов', 9, 'HR research 2026'),
    ('SAP SuccessFactors', 'keyword', 'Ищет как keywords так и semantic clusters', 8, 'SAP documentation'),
    ('Personio', 'keyword', 'Более keyword-based, меньше semantic — точное совпадение важнее', 8, 'Personio user reports'),
    ('Greenhouse', 'structure', 'Scoring по разделам: Impact, Speed, Teamwork, Communication', 9, 'Greenhouse blog'),
    ('ALL', 'format', 'Таблицы в CV = гарантированный parsing failure', 10, 'Industry standard'),
    ('ALL', 'format', 'Иконки/графика не читаются ATS', 10, 'Industry standard'),
    ('ALL', 'format', 'Формат даты должен быть MM.YYYY для DE рынка', 8, 'DE HR practice'),
    ('ALL', 'keyword', 'Keyword stuffing обнаруживается AI и снижает score', 9, 'ATS research 2026'),
    ('ALL', 'structure', 'Раздел "Skills" / "Kenntnisse" должен быть явным блоком', 9, 'ATS parsing rules'),
]


def init_database():
    """Инициализация базы данных"""
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Создание схемы БД...")
    conn.executescript(SCHEMA)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Загрузка базовых навыков...")
    cursor.executemany(
        """INSERT OR IGNORE INTO skills (skill_name, category, tier, market_demand, last_verified)
           VALUES (?, ?, ?, ?, date('now'))""",
        INITIAL_SKILLS
    )
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Загрузка ATS паттернов...")
    cursor.executemany(
        """INSERT OR IGNORE INTO ats_patterns (ats_system, pattern_type, description, effectiveness, source, verified_date)
           VALUES (?, ?, ?, ?, ?, date('now'))""",
        INITIAL_ATS_PATTERNS
    )
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ База данных успешно создана: {os.path.abspath(DB_PATH)}")
    print(f"   Навыков загружено: {len(INITIAL_SKILLS)}")
    print(f"   ATS паттернов загружено: {len(INITIAL_ATS_PATTERNS)}")


def show_stats():
    """Показать статистику БД"""
    if not os.path.exists(DB_PATH):
        print("❌ БД не найдена. Сначала запустите init_database()")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['companies', 'vacancies', 'cv_iterations', 'applications', 'interviews', 'skills', 'ats_patterns']
    
    print("\n📊 СТАТИСТИКА БАЗЫ ДАННЫХ:")
    print("=" * 50)
    for table in tables:
        try:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"   {table:25s}: {count:4d} записей")
        except sqlite3.OperationalError:
            print(f"   {table:25s}: таблица не найдена")
    
    # Статистика откликов
    try:
        status_stats = cursor.execute(
            "SELECT status, COUNT(*) FROM applications GROUP BY status ORDER BY COUNT(*) DESC"
        ).fetchall()
        if status_stats:
            print("\n📈 СТАТУСЫ ОТКЛИКОВ:")
            for status, count in status_stats:
                print(f"   {status:20s}: {count}")
    except Exception:
        pass
    
    conn.close()


if __name__ == '__main__':
    print("[START] HeadHunter ATS Optimization Database Setup")
    print("=" * 50)
    init_database()
    show_stats()
    print("\n[INFO] For database management use:")
    print("   - DB Browser for SQLite (GUI)")
    print("   - sqlite3 command line")
    print("   - Python sqlite3 / SQLAlchemy")
