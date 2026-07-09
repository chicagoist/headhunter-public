# ПУБЛИКАЦИЯ МОДЕЛИ HEADHUNTER — ОБЛАЧНЫЙ ДОСТУП
## Возможности и инструкции

> **Дата:** 09.07.2026  
> **Модель:** `headhunter:latest` (llama3.2:3b-instruct-q4_K_M + HeadHunter SYSTEM prompt)

---

## ⚠️ ВАЖНО — Личные данные в модели

В вашей модели через `SYSTEM`-промпт **зашиты в веса**:
```
[ИМЯ] | [EMAIL] | [TELEFON] | [ADRESSE]
```

> **Если выложить модель публично** — личные данные станут общедоступными  
> и извлекаемыми через простые промпты.  
> **Решение:** перед публикацией создать версию `headhunter-public`  
> без личных данных в SYSTEM-промпте.

---

## ВАРИАНТ 1 — Ollama Hub (ollama.com) 🟢

**Самый простой.** Модель публикуется в реестре Ollama — как Docker Hub, но для LLM.

### Шаги:
```powershell
# 1. Зарегистрироваться на https://ollama.com → создать аккаунт
# 2. Авторизоваться локально:
ollama login

# 3. Переименовать под свой namespace:
ollama cp headhunter YOUR_USERNAME/headhunter

# 4. Опубликовать:
ollama push YOUR_USERNAME/headhunter
```

### Использование с любого ПК:
```powershell
ollama pull YOUR_USERNAME/headhunter
ollama run YOUR_USERNAME/headhunter
```

### ✅ Плюсы
- Бесплатно, постоянный URL
- Установка одной командой на любом ПК
- Версионирование через теги (`:v1`, `:v2`)

### ❌ Минусы
- Только публичная публикация (нет приватных репозиториев на free tier)
- Личные данные в SYSTEM-промпте станут общедоступными

---

## ВАРИАНТ 2 — ngrok туннель (локальная → облако) 🟡

**Ollama работает на вашем ПК**, ngrok делает его доступным по публичному HTTPS-адресу.  
Личные данные никуда не передаются — модель остаётся локальной.

### Установка (один раз):
```powershell
# Установить ngrok:
winget install ngrok

# Зарегистрироваться на https://ngrok.com → получить Auth Token
# Настроить токен:
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Запуск:
```powershell
# Терминал 1 — запустить Ollama:
ollama serve

# Терминал 2 — открыть туннель:
ngrok http 11434

# Вывод будет примерно такой:
# Forwarding  https://abcd1234.ngrok-free.app → http://localhost:11434
```

### Использование из agent.py на другом ПК:
```python
# В DATABASE/04_AUTOMATION/agent.py изменить:
OLLAMA_URL = "https://abcd1234.ngrok-free.app"
```

### Использование через curl:
```bash
curl https://abcd1234.ngrok-free.app/api/chat -d '{
  "model": "headhunter",
  "messages": [{"role": "user", "content": "Analysiere diese Stelle: ..."}]
}'
```

### ✅ Плюсы
- Полностью бесплатно
- Личные данные не покидают ПК
- Работает прямо сейчас (~10 минут настройки)
- Приватный доступ (только у кого есть URL)

### ❌ Минусы
- URL меняется при каждом перезапуске (на free tier)
- Скорость ограничена i5-8365U (~4–8 tok/s)
- ПК должен быть включён и подключён к интернету
- Free tier ngrok: 1 агент, 1 туннель одновременно

### Постоянный URL (платный ngrok, $8/мес):
```powershell
# Статический домен — URL не меняется:
ngrok http --domain=headhunter.ngrok.app 11434
```

---

## ВАРИАНТ 3 — Google Colab + ngrok (бесплатный GPU T4) 🟡

Модель запускается на **бесплатном GPU Google (T4)** — в 5–10× быстрее i5.  
Доступ через ngrok-URL.

### Ноутбук Colab:
```python
# Ячейка 1 — установить Ollama:
import subprocess
subprocess.Popen(["curl", "-fsSL", "https://ollama.com/install.sh"])
!curl -fsSL https://ollama.com/install.sh | sh

# Ячейка 2 — запустить сервер в фоне:
import subprocess, time
subprocess.Popen(["ollama", "serve"])
time.sleep(3)

# Ячейка 3 — скачать базовую модель:
!ollama pull llama3.2:3b-instruct-q4_K_M

# Ячейка 4 — создать Modelfile и собрать headhunter:
modelfile_content = open("Modelfile.cpu").read()  # загрузить из проекта
with open("/tmp/Modelfile", "w") as f:
    f.write(modelfile_content)
!ollama create headhunter -f /tmp/Modelfile

# Ячейка 5 — туннель через ngrok:
!pip install pyngrok -q
from pyngrok import ngrok
ngrok.set_auth_token("YOUR_NGROK_TOKEN")
tunnel = ngrok.connect(11434)
print(f"Ollama URL: {tunnel.public_url}")
# → https://xxxx.ngrok-free.app

# Ячейка 6 — тест:
!curl {tunnel.public_url}/api/tags
```

### ✅ Плюсы
- Бесплатный GPU T4 (~30 tok/s — в 5× быстрее i5)
- Полный 5-шаговый цикл за ~1-2 минуты вместо 5-10

### ❌ Минусы
- Сессия Colab живёт максимум 12 часов
- Нужно перезапускать (модель не сохраняется)
- URL меняется при каждом перезапуске

---

## ВАРИАНТ 4 — Hugging Face Spaces (Gradio UI) 🟡

Веб-интерфейс к модели с постоянным URL на huggingface.co.

### Шаги:
1. Зарегистрироваться на [huggingface.co](https://huggingface.co)
2. Создать новый Space → тип: **Docker**
3. Загрузить GGUF файл модели (экспортировать из Ollama):
```powershell
# Найти путь к GGUF файлу:
$model_path = "$env:USERPROFILE\.ollama\models\blobs\"
# Файл ~2 GB с хешем sha256:...
```
4. Создать `app.py` с Gradio-интерфейсом для ввода вакансии
5. URL вида: `https://huggingface.co/spaces/USERNAME/headhunter`

### ✅ Плюсы
- Постоянный URL, красивый веб-интерфейс
- Бесплатный CPU-tier (медленно, но работает)

### ❌ Минусы
- Бесплатный CPU-tier: ~1-2 tok/s (очень медленно)
- Нужно экспортировать GGUF и настраивать Docker
- GPU Space: от $9/мес

---

## СРАВНИТЕЛЬНАЯ ТАБЛИЦА

| Вариант | Скорость | Цена | Сложность | Приватность | Постоянный URL |
|---|---|---|---|---|---|
| Ollama Hub | i5 ~4-8 tok/s | ✅ Бесплатно | ⭐ Легко | ❌ Публично | ✅ Да |
| ngrok туннель | i5 ~4-8 tok/s | ✅ Бесплатно | ⭐⭐ Легко | ✅ Приватно | ❌ Меняется |
| Colab + ngrok | T4 ~30 tok/s | ✅ Бесплатно | ⭐⭐⭐ Средне | ✅ Приватно | ❌ Меняется |
| HuggingFace | CPU ~1-2 tok/s | ✅ Бесплатно | ⭐⭐⭐ Средне | ✅ Настраиваемо | ✅ Да |

---

## 🏆 РЕКОМЕНДАЦИЯ

**Прямо сейчас** → **Вариант 2 (ngrok):**
```powershell
winget install ngrok
ngrok config add-authtoken YOUR_TOKEN   # с ngrok.com
ollama serve                             # терминал 1
ngrok http 11434                         # терминал 2
```
Готово за 10 минут. Модель остаётся приватной.

**Когда нужна скорость** → **Вариант 3 (Colab + GPU):**  
Бесплатный T4, полный цикл за 1-2 минуты.

**Для публичного API** → **Вариант 1 (Ollama Hub):**  
Сначала создать `headhunter-public` — версию без личных данных в SYSTEM-промпте:
```powershell
# Создать публичную версию (без имени/адреса/телефона в SYSTEM):
ollama create headhunter-public -f Modelfile.public
ollama push YOUR_USERNAME/headhunter-public
```

---

## Интеграция с agent.py

После получения URL — одна строка в `agent.py`:
```python
# Строка 60: изменить OLLAMA_URL:
OLLAMA_URL = "https://YOUR_URL.ngrok-free.app"   # ngrok
# или
OLLAMA_URL = "https://YOUR_URL.ngrok-free.app"   # Colab
```

Запуск как обычно:
```powershell
python DATABASE\04_AUTOMATION\agent.py --vacancy вакансия.txt --mode ollama
```
