# 🛠️ Python Automation Stack — HeadHunter 2026

> Технологический стек для автоматизации поиска работы

---

## ⚖️ ПРАВОВОЙ DISCLAIMER

> **ВАЖНО:** В Германии 2026 действует строгое регулирование:
> - **GDPR/DSGVO:** Не обрабатывай персональные данные третьих лиц без согласия
> - **Platform ToS:** LinkedIn, Indeed, XING запрещают автоматические отклики
> - **EU AI Act:** Human-in-the-Loop обязателен при принятии решений
>
> ✅ **РАЗРЕШЕНО:** Агрегация вакансий, ATS-анализ, генерация черновиков
> ❌ **ЗАПРЕЩЕНО:** Автоматическая рассылка откликов, scraping с аккаунта

---

## 📦 СТЕК БИБЛИОТЕК

### Tier 1 — Базовые (установить обязательно)
```bash
pip install httpx sqlite3 python-dotenv rich
```

| Библиотека | Назначение | Версия |
|---|---|---|
| `httpx` | Async HTTP клиент (замена requests) | ≥ 0.27 |
| `sqlite3` | Встроенная в Python, база данных | stdlib |
| `python-dotenv` | Управление API ключами | ≥ 1.0 |
| `rich` | Красивый вывод в консоль | ≥ 13.0 |

### Tier 2 — Анализ и AI
```bash
pip install langchain langchain-community chromadb sentence-transformers
```

| Библиотека | Назначение | Версия |
|---|---|---|
| `langchain` | LLM оркестрация | ≥ 0.3 |
| `langchain-community` | Connectors для Ollama, OpenAI | ≥ 0.3 |
| `chromadb` | Локальная Vector Database | ≥ 0.5 |
| `sentence-transformers` | Semantic embeddings | ≥ 3.0 |

### Tier 3 — Web Scraping (осторожно!)
```bash
pip install playwright beautifulsoup4 lxml
playwright install chromium
```

| Библиотека | Назначение | Версия |
|---|---|---|
| `playwright` | Browser automation (динамические страницы) | ≥ 1.45 |
| `beautifulsoup4` | HTML parsing | ≥ 4.12 |
| `lxml` | Быстрый XML/HTML parser | ≥ 5.0 |

### Tier 4 — Документы
```bash
pip install pypdf2 python-docx reportlab
```

| Библиотека | Назначение | Версия |
|---|---|---|
| `pypdf2` | Читать PDF резюме | ≥ 3.0 |
| `python-docx` | Создавать .docx документы | ≥ 1.1 |
| `reportlab` | Генерация PDF | ≥ 4.2 |

---

## 🤖 LOCAL LLM STACK

### Ollama (рекомендовано для privacy)
```bash
# Windows: Скачать Ollama с ollama.com
# Запустить сервис:
ollama serve

# Скачать модели:
ollama pull deepseek-r1:7b        # 7B параметров, быстро
ollama pull deepseek-r1:14b       # 14B параметров, лучше
ollama pull deepseek-coder:latest # Для кода
ollama pull llama3.1:8b           # Meta Llama 3.1

# Проверить доступность:
curl http://localhost:11434/api/tags
```

### LM Studio (GUI альтернатива)
```
1. Скачать: lmstudio.ai
2. Загрузить модель: DeepSeek-R1-Distill-Qwen-7B-Q8_0.gguf
3. Включить Local Server (port 1234)
4. Использовать OpenAI-совместимый API
```

---

## 🏗️ АРХИТЕКТУРА АГЕНТА (RAG + CV Optimization)

```
┌─────────────────────────────────────────────────┐
│              ДАННЫЕ КАНДИДАТА                    │
│  Lebenslauf.pdf → PyPDF2 → Text chunks          │
│  Zertifikate + Skills → Structured JSON          │
└──────────────────┬──────────────────────────────┘
                   │ embed
                   ▼
┌─────────────────────────────────────────────────┐
│           VECTOR DATABASE (ChromaDB)             │
│  Коллекция: "my_experience"                      │
│  Коллекция: "ats_patterns"                       │
│  Коллекция: "job_market_2026"                    │
└──────────────────┬──────────────────────────────┘
                   │
           ┌───────┴────────┐
           │   RAG Query     │
           └───────┬────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│            LOCAL LLM (Ollama/DeepSeek)           │
│  System: "Ты немецкий рекрутер 2026..."          │
│  Context: [relevant chunks from ChromaDB]         │
│  Prompt: [job description + analysis task]       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              OUTPUT + HUMAN REVIEW               │
│  1. ATS Score + Gap Analysis (JSON)              │
│  2. Optimized CV sections (текст для проверки)   │
│  3. Anschreiben draft (финальная правка человека) │
│  4. SQLite DB update (лог отклика)               │
└─────────────────────────────────────────────────┘
```

---

## 📋 WORKFLOW АВТОМАТИЗАЦИИ (разрешённый)

### Фаза 1: Сбор вакансий (Aggregation)
```python
# 1. Мониторинг RSS-фидов платформ (без нарушения ToS)
# StepStone RSS: stepstone.de/stellenangebote/rss
# Indeed RSS:    indeed.com/rss?q=java+spring&l=Deutschland
# LinkedIn:      Использовать Email Alert (настроить в профиле)

# 2. Парсить полученные данные
# 3. Сохранять в SQLite (таблица vacancies)
# 4. Отмечать новые вакансии для анализа
```

### Фаза 2: ATS Score Analysis (cv_optimizer_prompt.py)
```python
# 1. Для каждой новой вакансии:
#    a. Извлечь текст вакансии
#    b. Запустить gap-analysis через Ollama
#    c. Получить ATS Score + missing keywords
#    d. Сохранить в cv_iterations таблицу

# 2. Фильтрация:
#    - ATS Score >= 60 → кандидат на отклик
#    - ATS Score >= 80 → ПРИОРИТЕТНЫЙ отклик
#    - ATS Score < 40 → не тратить время
```

### Фаза 3: CV Adaptation (ручная с AI-помощью)
```python
# 1. Взять Lebenslauf_Template_ATS.md как базу
# 2. Запустить cv_optimizer_prompt.py --mode rewrite
# 3. ПРОВЕРИТЬ каждое изменение (Human-in-the-Loop)
# 4. Создать PDF через Word или LibreOffice
# 5. Проверить: одна колонка, чистый текст, правильные даты
```

### Фаза 4: Anschreiben Generation
```python
# 1. Запустить Prompt №3 из Prompt_Library.md
# 2. Использовать hook из ATS Score анализа
# 3. ОБЯЗАТЕЛЬНО добавить 1 личную деталь о компании (Human-in-the-Loop)
# 4. Финальная проверка: клише, длина, немецкий стиль
```

### Фаза 5: Отправка (ТОЛЬКО ВРУЧНУЮ)
```
✅ ВСЕГДА ВРУЧНУЮ:
   - Через портал компании (не автозаполнение)
   - Или Email (с персонализацией)
   - НИКОГДА: browser bot, auto-apply скрипт
```

---

## 📊 ПРИМЕРЫ ЗАПРОСОВ К БД (аналитика)

```sql
-- Топ компании по ATS Score
SELECT c.name, AVG(ci.ats_score) as avg_score, COUNT(*) as attempts
FROM companies c
JOIN vacancies v ON c.company_id = v.company_id
JOIN cv_iterations ci ON v.vacancy_id = ci.vacancy_id
GROUP BY c.company_id
ORDER BY avg_score DESC;

-- Статистика откликов по статусам
SELECT status, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM applications), 1) as pct
FROM applications
GROUP BY status;

-- Конверсия по платформам
SELECT v.source_platform,
       COUNT(a.application_id) as total,
       SUM(CASE WHEN a.status NOT IN ('REJECTED_AUTO','REJECTED_HR') THEN 1 ELSE 0 END) as positive
FROM vacancies v
JOIN cv_iterations ci ON v.vacancy_id = ci.vacancy_id
JOIN applications a ON ci.iteration_id = a.iteration_id
GROUP BY v.source_platform;

-- Вакансии требующие follow-up
SELECT c.name, v.job_title, a.follow_up_date, a.status
FROM applications a
JOIN cv_iterations ci ON a.iteration_id = ci.iteration_id
JOIN vacancies v ON ci.vacancy_id = v.vacancy_id
JOIN companies c ON v.company_id = c.company_id
WHERE a.follow_up_date <= date('now') AND a.status = 'PENDING'
ORDER BY a.follow_up_date;
```

---

## 🔒 БЕЗОПАСНОСТЬ И ПРИВАТНОСТЬ

```
✅ БЕЗОПАСНАЯ ПРАКТИКА:
   • Хранить API ключи в .env (добавить в .gitignore!)
   • Использовать Ollama/локальный LLM для чувствительных данных
   • Шифровать SQLite БД если содержит личные данные
   • Не синхронизировать ats_optimization.db с облаком без шифрования

✅ .env файл (шаблон):
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=deepseek-r1:7b
```
