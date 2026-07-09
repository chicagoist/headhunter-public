import urllib.request, json, sys, io, os, ssl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_openai_compat(name, url, key, model, msg="Reply: OK"):
    """Tests an OpenAI-compatible API endpoint."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": msg}],
        "max_tokens": 10
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            data = json.loads(r.read())
        content = data['choices'][0]['message']['content']
        print(f"  [{name}] OK -> {content[:60]}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')[:150]
        print(f"  [{name}] HTTP {e.code}: {body}")
        return False
    except Exception as e:
        print(f"  [{name}] ERROR: {str(e)[:100]}")
        return False

print("=== Backend Availability Check ===\n")

# Mistral
test_openai_compat(
    "Mistral mistral-small",
    "https://api.mistral.ai/v1/chat/completions",
    os.environ.get('MISTRAL_API_KEY', ''),
    "mistral-small-latest"
)

# DashScope / Qwen (OpenAI-compatible endpoint)
test_openai_compat(
    "Qwen/DashScope qwen-plus",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    os.environ.get('DASHSCOPE_API_KEY', ''),
    "qwen-plus"
)

# GROQ with different key approach
groq_key = os.environ.get('GROQ_API_KEY', '')
test_openai_compat(
    "GROQ llama-3.3-70b",
    "https://api.groq.com/openai/v1/chat/completions",
    groq_key,
    "llama-3.3-70b-versatile"
)

# Google Generative AI REST - try with current key format
google_key = os.environ.get('GOOGLE_API_KEY', '')
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={google_key}"
payload = json.dumps({"contents": [{"parts": [{"text": "Reply: OK"}]}]}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=12) as r:
        data = json.loads(r.read())
    text = data['candidates'][0]['content']['parts'][0]['text']
    print(f"  [Google Gemini 2.0 Flash] OK -> {text[:60]}")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')[:200]
    print(f"  [Google Gemini] HTTP {e.code}: {body[:120]}")
except Exception as e:
    print(f"  [Google Gemini] ERROR: {str(e)[:100]}")
