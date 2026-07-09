# HeadHunter Agent v2.1 — Руководство пользователя
## Полная инструкция для начинающих

> **Для кого:** Для тех, кто никогда не видел этот проект  
> **Что это:** ИИ-агент, который читает описание вакансии и автоматически создаёт адаптированное резюме (Lebenslauf) + сопроводительное письмо (Anschreiben) + PDF  
> **Язык вакансий:** Немецкий рынок труда (DE)  
> **Время на один отклик:** ~2-3 минуты (вместо 2-3 часов вручную)

---

## Что делает агент — простыми словами

```
ВЫ даёте:              АГЕНТ делает:                     ВЫ получаете:
─────────────          ──────────────────────────────    ──────────────────
Текст вакансии    →    Анализирует требования       →    lebenslauf.md
Ваше резюме       →    Считает ATS-Score (0-100)    →    lebenslauf.pdf
Ваш профиль       →    Переписывает резюме под CV   →    anschreiben.md
                  →    Создаёт письмо без клише     →    ANALYSE_REPORT.md
```

**ATS-Score** — оценка, насколько ваше резюме пройдёт через автоматический фильтр работодателя:
- **70-100** → 🟢 Отправлять немедленно
- **50-69**  → 🟡 Доработать резюме, потом отправлять
- **< 50**   → 🔴 Вакансия не подходит, пропустить

---

## Часть 1: Установка (делается один раз)

> 📘 **Полный кроссплатформенный гайд:** [`SETUP.md`](SETUP.md) — установка на Windows/Linux/macOS, таблица PDF-движков, решение проблем с зависимостями.

### Шаг 1.1 — Проверить Python

Откройте PowerShell (Win+X → Terminal) и введите:
```powershell
python --version
```
Должно показать `Python 3.10` или выше. Если нет — установите с [python.org](https://python.org).

### Шаг 1.2 — Установить зависимости

Все Python-зависимости перечислены в [`requirements.txt`](requirements.txt):

```powershell
pip install -r requirements.txt
```

> ⚠️ На Linux с externally-managed Python: `pip install --break-system-packages -r requirements.txt`

### Шаг 1.3 — Установить PDF-конвертер

```powershell
# Windows:
winget install wkhtmltopdf
winget install JohnMacFarlane.Pandoc

# Linux:
sudo apt install wkhtmltopdf pandoc

# macOS:
brew install wkhtmltopdf pandoc
```

После установки **перезапустите PowerShell/Terminal**.

> 💡 Подробнее о выборе PDF-движка под вашу ОС — см. [`SETUP.md`](SETUP.md).

### Шаг 1.4 — Получить бесплатный API-ключ

Агент использует ИИ для генерации текстов. Рекомендуется **Mistral AI** (бесплатно, отличный немецкий):

1. Открыть: https://console.mistral.ai
2. Sign up (бесплатно)
3. API Keys → Create new key
4. Скопировать ключ

Сохранить ключ как переменную окружения:
```powershell
# Добавить постоянно (один раз):
[System.Environment]::SetEnvironmentVariable("MISTRAL_API_KEY", "ВАШ_КЛЮЧ", "User")
# Перезапустить PowerShell!
```

**Или через OpenRouter** (Google/Meta/GPT модели):
```powershell
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-...", "User")
```

### Шаг 1.5 — Открыть папку проекта

```powershell
cd /home/user/headhunter-public
```

---

## Часть 2: Настройка под ВАШЕГО кандидата

> **Это самый важный шаг.** Агент читает два файла. Без правильного заполнения результат будет слабым.

### Шаг 2.1 — Заполнить профиль кандидата

Открыть файл: `DATABASE\00_CANDIDATE_PROFILE\kandidat_profil.md`

```yaml
# Пример заполнения:
name: "Иван Иванов"
email: "ivan@example.com"
phone: "+49 123 4567890"
address: "Musterstraße 1, 10115 Berlin"
linkedin: "linkedin.com/in/ivanivanov"

ziel_position: "Junior IT-Administrator"
verfuegbar_ab: "01.10.2026"
sprachen:
  - "Deutsch: B2"
  - "Englisch: B1"

hard_skills:
  - "Windows Server 2019/2022"
  - "Linux (Ubuntu, Debian)"
  - "Active Directory"
  - "PowerShell, Bash"
  - "Microsoft Azure (AZ-900)"

berufserfahrung:
  - firma: "Meine Firma GmbH"
    zeitraum: "01/2020 – heute"
    rolle: "IT-Techniker"
    aufgaben:
      - "Administration von Windows-Servern"
      - "Benutzerbetreuung 1st/2nd Level"

zertifikate:
  - "Microsoft AZ-900 (2024)"
```

### Шаг 2.2 — Обновить мастер-резюме

Открыть: `DATABASE\00_CANDIDATE_PROFILE\lebenslauf_master.md`

Это базовый Lebenslauf в Markdown. Правила:
- Хронологический порядок (новейшее → старейшее)
- Формат дат: `MM/YYYY`
- Bullet points: `[Глагол] + [Технология] + [Результат]`
- Максимум 2 страницы A4

Конвертация из Word:
```powershell
pandoc "МоёРезюме.docx" -o "DATABASE\00_CANDIDATE_PROFILE\lebenslauf_master.md"
```

---

## Часть 3: Запуск агента на реальной вакансии

### Шаг 3.1 — Найти вакансию

Сайты для поиска:
- [stepstone.de](https://stepstone.de)
- [indeed.de](https://indeed.de)
- [xing.de](https://xing.de)
- [arbeitsagentur.de](https://arbeitsagentur.de)
- [linkedin.com/jobs](https://linkedin.com/jobs)

### Шаг 3.2 — Сохранить текст вакансии

Скопируйте **весь текст** вакансии в `.txt` файл.

Пример: `C:\Projects\OpenClaw\HeadHunter\PROJECT_beta\siemens_admin.txt`

> 💡 Чем больше текста — тем лучше анализ. Копируйте всё, включая "Was wir bieten".

### Шаг 3.3 — Запустить агент

```powershell
cd /home/user/headhunter-public

# Через Mistral (рекомендуется):
python DATABASE\04_AUTOMATION\agent.py --vacancy siemens_admin.txt --mode mistral

# Или через OpenRouter (Google Gemma / Meta Llama):
python DATABASE\04_AUTOMATION\agent.py --vacancy siemens_admin.txt --mode openrouter

# Тест без ИИ (мгновенно, проверка структуры):
python DATABASE\04_AUTOMATION\agent.py --vacancy siemens_admin.txt --mode dry-run
```

### Шаг 3.4 — Что видно в консоли

```
============================================================
  HeadHunter Agent v2.1
============================================================

[1/5] Lade Kandidatenprofil und Lebenslauf-Vorlage...
     OK

[2/5] STEP 1 — Vacancy-Analyse...         ← Читает вакансию
     [api.mistral.ai] Modell: mistral-large-latest
     [OK] Tokens: 961 in / 460 out
     Firma: Siemens AG | Stelle: IT-Administrator (m/w/d)

[3/5] STEP 2 — Match & Score...           ← Считает совпадение
     [OK] Tokens: 1295 in / 630 out
     ATS Score: 75/100 | Empfehlung: JETZT_BEWERBEN  ✅

[4/5] STEP 3 — Lebenslauf adaptieren...   ← Переписывает резюме
     [OK] Tokens: 1994 in / 1372 out

[4/5] STEP 4 — Anschreiben erstellen...   ← Пишет письмо
     [OK] Tokens: 1286 in / 1288 out

[5/5] STEP 5 — Output speichern...        ← Сохраняет файлы
  [GESPEICHERT] lebenslauf_Siemens_AG.md
  [GESPEICHERT] anschreiben_Siemens_AG.md
  [PDF] Erstellt: lebenslauf_Siemens_AG.pdf
  [GESPEICHERT] ANALYSE_REPORT.md

============================================================
  FERTIG! ATS Score: 75/100 | JETZT_BEWERBEN
============================================================
```

**Время:** ~90-120 секунд.

### Шаг 3.5 — Найти результаты

```
OUTPUT\Bewerbungen\[DATUM]_[FIRMA]_[STELLE]\
    ├── lebenslauf_[Firma].md       ← Резюме (Markdown)
    ├── lebenslauf_[Firma].pdf      ← Резюме (PDF, готов к отправке)
    ├── anschreiben_[Firma].md      ← Сопроводительное письмо
    └── ANALYSE_REPORT.md           ← Анализ: что совпало, что нет
```

### Шаг 3.6 — Проверить вручную (обязательно!)

**Чеклист Lebenslauf:**
- [ ] Все факты верны (даты, компании, должности)?
- [ ] Ключевые слова из вакансии присутствуют?
- [ ] Не более 2 страниц?

**Чеклист Anschreiben:**
- [ ] Правильное имя рекрутера?
- [ ] Конкретный повод — почему именно эта компания?
- [ ] Нет фраз "Hiermit bewerbe ich mich..." или "Ich bin Teamplayer"?
- [ ] Указана дата доступности?
- [ ] Ровно ~1 страница?

---

## Часть 4: Тестовый пример (реальный результат)

### Входные данные:
```
Вакансия: Junior IT-Administrator (m/w/d)
Компания: TechNet Solutions GmbH — Frankfurt am Main / Hybrid
Требования: Windows Server, Linux, Azure AZ-900, Active Directory,
            PowerShell, 1st/2nd Level Support
Зарплата: 38.000–45.000 €/Jahr
```

### Результат (ATS Score 75/100):

| | |
|---|---|
| **Empfehlung** | ✅ **JETZT BEWERBEN** |
| Tier1 ✅ vorhanden | Windows Server, Linux, Azure, AD, PowerShell |
| Tier2 ✅ vorhanden | Hyper-V, Python, IT-Sicherheit/DSGVO |
| ❌ Fehlend | Docker, CCNA, Ticketsystem |
| Stärken | AZ-900-Zertifizierung, 10J Sysadmin-Erfahrung |
| Red Flags | Keine formale IT-Ausbildung |

**Фрагмент сгенерированного Anschreiben:**
> *"Als langjähriger Freelance-Systemadministrator mit fundierten Kenntnissen in Windows Server 2019/2022 und Linux (Debian/Ubuntu) sehe ich in der Stelle bei TechNet Solutions die ideale Gelegenheit, meine Expertise in einem dynamischen Team einzubringen – besonders reizt mich Ihr Weiterbildungsbudget von 1.500 €/Jahr..."*

**Время работы:** ~110 сек | **Стоимость:** бесплатно

---

## Часть 5: Адаптация для ДРУГИХ пользователей

### 5.1 — Что заменить

| Файл | Что изменить |
|---|---|
| `DATABASE/00_CANDIDATE_PROFILE/kandidat_profil.md` | Личные данные, навыки, опыт |
| `DATABASE/00_CANDIDATE_PROFILE/lebenslauf_master.md` | Полное резюме в Markdown |
| `DATABASE/04_AUTOMATION/agent.py` (строка ~537) | Адрес кандидата в шаблоне письма |

### 5.2 — Пошаговая адаптация

**Шаг A: Персональные данные** в `kandidat_profil.md`:
```yaml
name: "Ваше Имя Фамилия"
email: "your@email.de"
phone: "+49 ..."
address: "Ihre Straße 1, 10115 Berlin"
```

**Шаг B: Навыки** — заменить весь раздел `hard_skills`, `soft_skills`, `berufserfahrung`, `ausbildung`, `zertifikate`.

**Шаг C: Конвертировать резюме из Word**:
```powershell
pandoc "МоёРезюме.docx" -o "DATABASE\00_CANDIDATE_PROFILE\lebenslauf_master.md"
```

**Шаг D: Обновить адрес в шаблоне** — в `agent.py` найти `[VORNAME NACHNAME]` и `[STRASSE, PLZ STADT]` (Ctrl+F) и заменить на свои данные.

**Шаг E: Тест**:
```powershell
python DATABASE\04_AUTOMATION\agent.py --vacancy тест.txt --mode dry-run
```

### 5.3 — Примеры для разных профилей

**Java-разработчик:**
```yaml
ziel_position: "Junior Java Developer"
hard_skills: ["Java 21", "Spring Boot", "REST API", "PostgreSQL", "Git", "Maven"]
```

**Data Analyst:**
```yaml
ziel_position: "Data Analyst"
hard_skills: ["Python", "SQL", "Pandas", "Tableau", "Power BI", "Excel"]
```

**Переквалификация из другой сферы:**
```yaml
weiterbildung:
  - "Google IT Support Certificate (Coursera, 2024)"
  - "SQL Bootcamp (Udemy, 2024)"
transfer_argumente:
  - "5 Jahre Kundensupport → Kommunikation im IT-Helpdesk"
  - "Buchhaltung → Strukturiertes Denken für Datenbankdesign"
```

### 5.4 — Поддерживаемые рынки

| Рынок | Статус | Примечание |
|---|---|---|
| Германия (DE) | ✅ Полная поддержка | Основной режим |
| Австрия (AT) | ✅ Работает | Те же правила |
| Швейцария (CH) | ✅ DE/FR вакансии | Язык определяется автоматически |

---

## Часть 6: Справочник команд

```powershell
# Перейти в папку проекта:
cd /home/user/headhunter-public

# Основные команды:
python DATABASE\04_AUTOMATION\agent.py --vacancy ВАКАНСИЯ.txt --mode mistral
python DATABASE\04_AUTOMATION\agent.py --vacancy ВАКАНСИЯ.txt --mode openrouter
python DATABASE\04_AUTOMATION\agent.py --vacancy ВАКАНСИЯ.txt --mode dry-run

# Конкретная модель:
python DATABASE\04_AUTOMATION\agent.py --vacancy ВАКАНСИЯ.txt --mode openrouter --model google/gemma-4-31b-it:free

# Явный API-ключ:
python DATABASE\04_AUTOMATION\agent.py --vacancy ВАКАНСИЯ.txt --mode mistral --apikey ВАШ_КЛЮЧ

# Справка:
python DATABASE\04_AUTOMATION\agent.py --help

# Проверка доступных бэкендов:
python DATABASE\04_AUTOMATION\check_backends.py
```

---

## Часть 7: Решение проблем

| Проблема | Решение |
|---|---|
| `FileNotFoundError: kandidat_profil.md` | Запускайте из корня проекта (`headhunter-public/`), не из `DATABASE\04_AUTOMATION` |
| `HTTP 429` | Вечерняя нагрузка. Подождите 10-15 мин или запустите утром |
| `HTTP 401 Unauthorized` | Неверный ключ. Проверьте: `$env:MISTRAL_API_KEY` |
| PDF пустой | Проверьте: `wkhtmltopdf --version` und `pandoc --version` |
| Кириллица "?????" | Запускайте: `$env:PYTHONIOENCODING='utf-8'; python ...` |
| JSON parse failed | Агент автоматически повторит с другой моделью |

---

## Часть 8: API-ключи — где получить (бесплатно)

| Сервис | URL | Лимит | Режим |
|---|---|---|---|
| **Mistral AI** | console.mistral.ai | Бесплатный tier | `--mode mistral` |
| **OpenRouter** | openrouter.ai | 200 запросов/день | `--mode openrouter` |

```powershell
# Установить ключи постоянно:
[System.Environment]::SetEnvironmentVariable("MISTRAL_API_KEY",    "ваш_ключ", "User")
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "sk-or-v1-...", "User")

# Перезапустить PowerShell, затем проверить:
echo $env:MISTRAL_API_KEY
```

---

> **Оптимальный workflow:** `--mode mistral` основной → `--mode openrouter` резервный → `--mode dry-run` для теста структуры.
>
> **Human-in-the-Loop:** Агент создаёт качественные черновики — финальное решение всегда за вами. Проверяйте факты перед отправкой.
>
> **GDPR / Datenschutz:** При использовании облачных API ваши данные обрабатываются на их серверах. Для максимальной приватности: `winget install Ollama.Ollama` → `ollama pull llama3.3` → `--mode ollama`.

---

## Часть 9: Выбор модели ИИ — рекомендации по результатам тестов

> Протестировано на реальных вакансиях (08.07.2026). Критерии: немецкий язык, JSON-точность, следование инструкциям.

### Требования задачи

- Генерация текста на **немецком языке** (Hochdeutsch, DIN 5008)
- Строгий **JSON-вывод** (STEP 1 и 2)
- Длинные связные тексты (~1000–1500 токенов на выход)
- Следование промпт-шаблону

---

### 🥇 Mistral Large Latest — **лучший выбор**

```powershell
--mode mistral   # автоматически: mistral-large-latest
```

| Критерий | Оценка |
|---|---|
| Немецкий язык | ⭐⭐⭐⭐⭐ — обучен на EU-данных, DIN-стиль естественный |
| JSON-точность | ⭐⭐⭐⭐⭐ — всегда валидный JSON без обрезки |
| Следование инструкциям | ⭐⭐⭐⭐⭐ — строго соблюдает шаблон |
| Скорость | ⭐⭐⭐⭐ — ~90 сек на весь цикл |
| Лимит (бесплатно) | Generous free tier |

> Результат: 5 шагов × 2 прогона = **0 ошибок**, чистый JSON каждый раз.

---

### 🥈 Google Gemma 4 31B (via OpenRouter) — **отличный резерв**

```powershell
--mode openrouter   # google/gemma-4-31b-it:free
```

| Критерий | Оценка |
|---|---|
| Немецкий язык | ⭐⭐⭐⭐⭐ — Google multilingual, очень хороший |
| JSON-точность | ⭐⭐⭐⭐ — иногда добавляет ```markdown``` обёртку (чиним автоматически) |
| Следование инструкциям | ⭐⭐⭐⭐ — хорошо |
| Скорость | ⭐⭐⭐⭐ — ~110 сек |
| Лимит (бесплатно) | 200 запросов/день на OpenRouter |

> Результат: **ATS Score 78.75/100** — чуть выше чем Mistral (75). Gemma немного агрессивнее оценивает совпадения.

---

### 🥉 Meta Llama 3.3 70B — **надёжный fallback**

```powershell
--mode openrouter --model meta-llama/llama-3.3-70b-instruct:free
```

| Критерий | Оценка |
|---|---|
| Немецкий язык | ⭐⭐⭐⭐ — хороший, но EN-ориентирован |
| JSON-точность | ⭐⭐⭐⭐⭐ — очень надёжный JSON |
| Следование инструкциям | ⭐⭐⭐⭐⭐ — лучший из всех |
| Доступность | ⭐⭐⭐ — 429 при пиковой нагрузке |

---

### ❌ Что не работает / не подходит

| Модель | Проблема |
|---|---|
| `openai/gpt-oss-120b:free` | 429 почти всегда (пиковая нагрузка) |
| `openai/gpt-oss-20b:free` | Слишком маленький — обрезает JSON |
| `meta-llama/llama-3.2-3b-instruct:free` | 3B — слабый немецкий, нет для production |
| `GROQ` | 403 Forbidden на нашем аккаунте |
| `DeepSeek` | 402 — баланс исчерпан |

---

### Итоговая схема выбора

```
ОСНОВНОЙ:   --mode mistral         → Mistral Large Latest
              ↓ (если недоступен)
РЕЗЕРВ 1:   --mode openrouter      → Gemma 4 31B (auto-fallback внутри агента)
              ↓ (если 429 везде)
РЕЗЕРВ 2:   Подождать утра (~09:00 CEST) — нагрузка на серверы минимальна
              ↓ (всегда)
ТЕСТ:       --mode dry-run         → без LLM, мгновенно
```

> **Вывод:** Для немецкого рынка труда `mistral-large-latest` — оптимальный выбор. Бесплатный tier без жёстких лимитов.