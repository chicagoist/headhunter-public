# Modelfile — Использование и установка

Кастомные Ollama-модели для HeadHunter Agent v2.0.

---

## Быстрый старт

### 1. Установить Ollama

```powershell
winget install Ollama.Ollama
```

### 2. Загрузить базовую модель

```powershell
# Рекомендуется — баланс качества и скорости (~4 GB RAM):
ollama pull deepseek-r1:7b

# Лучшее качество немецкого (~8 GB RAM):
ollama pull deepseek-r1:14b

# Надёжный JSON, быстро (~4 GB):
ollama pull mistral:7b-instruct-v0.3

# Топ-качество немецкого (~8 GB):
ollama pull qwen2.5:14b
```

### 3. Создать кастомную модель

```powershell
# Стандартная (deepseek-r1:7b):
ollama create headhunter -f Modelfile

# 14B версия (лучше, если есть ≥ 16 GB RAM):
ollama create headhunter-14b -f Modelfile.14b

# Mistral-версия (надёжный JSON):
ollama create headhunter-mistral -f Modelfile.mistral

# Qwen-версия (отличный немецкий):
ollama create headhunter-qwen -f Modelfile.qwen
```

### 4. Запустить агент

```powershell
# Через agent.py:
python DATABASE\04_AUTOMATION\agent.py --vacancy DATEI.txt --mode ollama

# Напрямую через Ollama CLI:
ollama run headhunter

# Через API (для интеграций):
curl http://localhost:11434/api/chat -d '{
  "model": "headhunter",
  "messages": [{"role": "user", "content": "Analysiere diese Stelle: ..."}]
}'
```

---

## Файлы

| Файл | Базовая модель | RAM | Качество DE | Рекомендация |
|---|---|---|---|---|
| `Modelfile` | deepseek-r1:7b | ~4 GB | ⭐⭐⭐⭐ | Стандарт |
| `Modelfile.14b` | deepseek-r1:14b | ~8 GB | ⭐⭐⭐⭐⭐ | Лучшее |
| `Modelfile.mistral` | mistral:7b-instruct | ~4 GB | ⭐⭐⭐⭐ | Надёжный JSON |
| `Modelfile.qwen` | qwen2.5:14b | ~8 GB | ⭐⭐⭐⭐⭐ | Топ-немецкий |

---

## Параметры (можно менять в Modelfile)

| Параметр | Значение | Описание |
|---|---|---|
| `temperature` | 0.2 | Низкое = точный JSON, высокое = творческий текст |
| `num_ctx` | 8192 | Контекстное окно (токены) |
| `num_predict` | 3000 | Максимум токенов в ответе |
| `top_p` | 0.90 | Nucleus sampling |
| `repeat_penalty` | 1.15 | Против зацикливания |
| `mirostat` | 2 | Когерентность длинных текстов |

---

## Интеграция с agent.py

Режим `--mode ollama` автоматически использует `http://localhost:11434`.

Чтобы использовать кастомную модель вместо дефолтной:

```python
# В agent.py — изменить DEFAULT_OLLAMA_MODEL:
DEFAULT_OLLAMA_MODEL = "headhunter"  # вместо "deepseek-r1:7b"
```

Или через переменную окружения:

```powershell
$env:OLLAMA_MODEL = "headhunter"
python DATABASE\04_AUTOMATION\agent.py --vacancy test.txt --mode ollama
```
