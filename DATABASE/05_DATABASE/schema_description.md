# 🗃️ Схема Базы Данных ATS Optimization

> Описание всех таблиц SQLite базы данных ats_optimization.db

---

## 📊 ERD (Entity-Relationship Diagram)

```
┌──────────────┐    ┌──────────────────┐    ┌────────────────────┐
│  COMPANIES   │    │    VACANCIES     │    │   CV_ITERATIONS    │
│──────────────│    │──────────────────│    │────────────────────│
│ company_id ◄─┼────│ company_id       │◄───│ vacancy_id         │
│ name         │    │ vacancy_id ◄─────┼────┤ iteration_id       │
│ industry     │    │ job_title        │    │ ats_score          │
│ size         │    │ job_url          │    │ keyword_match_pct  │
│ ats_system   │    │ source_platform  │    │ din_spec_compliant │
│ betriebsrat  │    │ location         │    │ human_reviewed     │
│ kununu_score │    │ salary_min/max   │    │ ai_tools_used      │
└──────────────┘    │ required_skills  │    └─────────┬──────────┘
                    │ job_description  │              │
                    └──────────────────┘              │
                                                      ▼
                    ┌──────────────────┐    ┌────────────────────┐
                    │   INTERVIEWS     │    │   APPLICATIONS     │
                    │──────────────────│    │────────────────────│
                    │ interview_id     │    │ application_id ◄───│
                    │ application_id ◄─┼────│ iteration_id       │
                    │ interview_type   │    │ application_date   │
                    │ round_number     │    │ status             │
                    │ questions_asked  │    │ response_date      │
                    │ outcome          │    │ follow_up_date     │
                    └──────────────────┘    │ contact_person     │
                                           └────────────────────┘

┌──────────────────┐    ┌────────────────────┐
│     SKILLS       │    │   ATS_PATTERNS     │
│──────────────────│    │────────────────────│
│ skill_id         │    │ pattern_id         │
│ skill_name       │    │ ats_system         │
│ category         │    │ pattern_type       │
│ tier (1/2/3)     │    │ description        │
│ market_demand    │    │ effectiveness      │
└──────────────────┘    └────────────────────┘
```

---

## 📋 ОПИСАНИЕ ПОЛЕЙ

### companies
| Поле | Тип | Описание |
|---|---|---|
| `company_id` | INTEGER PK | Уникальный ID |
| `name` | TEXT | Название компании |
| `industry` | TEXT | Отрасль |
| `size` | TEXT | startup/SMB/Mittelstand/Konzern |
| `ats_system` | TEXT | Используемая ATS система |
| `betriebsrat` | INTEGER | 1 = есть Betriebsrat |
| `kununu_score` | REAL | Рейтинг на Kununu.com |

### vacancies
| Поле | Тип | Описание |
|---|---|---|
| `vacancy_id` | INTEGER PK | Уникальный ID |
| `job_title` | TEXT | Название позиции |
| `source_platform` | TEXT | LinkedIn/StepStone/XING/Indeed/Direct |
| `remote_option` | TEXT | onsite/hybrid/remote |
| `salary_min/max` | INTEGER | Зарплатная вилка (€ в год) |
| `required_skills` | TEXT | Требуемые навыки (comma-sep) |
| `date_found` | DATE | Когда найдена вакансия |

### applications — СТАТУСЫ
```
PENDING          → Отправлен, ждём ответа
ATS_REVIEW       → Проходит ATS фильтрацию
HR_REVIEW        → Рецензируется HR
PHONE_SCREEN     → Назначен телефонный звонок
TECH_INTERVIEW   → Технический интервью
ASSESSMENT       → Техническое задание/тест
FINAL_INTERVIEW  → Финальный интервью
OFFER            → Получено предложение ✅
REJECTED_AUTO    → Автоматический отказ (ATS)
REJECTED_HR      → Отказ от HR
REJECTED_INTERVIEW → Отказ после интервью
WITHDRAWN        → Отозвал заявку сам
BLACKLISTED      → Компания не подходит (внутренняя метка)
```

---

## 🔍 ПОЛЕЗНЫЕ ЗАПРОСЫ

### Недельный дайджест
```sql
SELECT 
    date(application_date) as day,
    COUNT(*) as applications,
    SUM(CASE WHEN status = 'HR_REVIEW' THEN 1 ELSE 0 END) as positive
FROM applications
WHERE application_date >= date('now', '-7 days')
GROUP BY date(application_date)
ORDER BY day;
```

### Требующие follow-up сегодня
```sql
SELECT c.name, v.job_title, a.follow_up_date, a.status, a.contact_person
FROM applications a
JOIN cv_iterations ci ON a.iteration_id = ci.iteration_id
JOIN vacancies v ON ci.vacancy_id = v.vacancy_id
JOIN companies c ON v.company_id = c.company_id
WHERE a.follow_up_date = date('now') AND a.status IN ('PENDING', 'ATS_REVIEW')
ORDER BY a.follow_up_date;
```

### Конверсионная воронка
```sql
WITH funnel AS (
    SELECT 
        'Total' as stage, COUNT(*) as count FROM applications
    UNION ALL
    SELECT 'HR Review+', COUNT(*) FROM applications 
        WHERE status NOT IN ('PENDING','ATS_REVIEW','REJECTED_AUTO')
    UNION ALL
    SELECT 'Interview', COUNT(*) FROM applications 
        WHERE status IN ('PHONE_SCREEN','TECH_INTERVIEW','ASSESSMENT','FINAL_INTERVIEW','OFFER')
    UNION ALL
    SELECT 'Offer', COUNT(*) FROM applications WHERE status = 'OFFER'
)
SELECT stage, count, 
       ROUND(count * 100.0 / MAX(count) OVER (), 1) as pct
FROM funnel;
```
