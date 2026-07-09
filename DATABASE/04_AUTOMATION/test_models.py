import httpx, sys, io, time, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

APIKEY = os.environ.get('OPENROUTER_API_KEY', 'YOUR_KEY_HERE')  # Set via: export OPENROUTER_API_KEY=sk-or-v1-...
MODELS = [
    'openai/gpt-oss-120b:free',
    'qwen/qwen3-next-80b-a3b-instruct:free',
    'nousresearch/hermes-3-llama-3.1-405b:free',
    'nvidia/nemotron-3-super-120b-a12b:free',
    'nvidia/nemotron-3-ultra-550b-a55b:free',
    'google/gemma-4-31b-it:free',
    'meta-llama/llama-3.3-70b-instruct:free',
]

TEST_MSG = 'Reply ONLY with valid JSON, no markdown: {"status": "ok", "model": "write your model slug here"}'

print("Testing free OpenRouter models...\n")
working = []
for model in MODELS:
    print(f"  {model} ...", end=" ", flush=True)
    try:
        r = httpx.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={'Authorization': f'Bearer {APIKEY}'},
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': TEST_MSG}],
                'max_tokens': 60,
                'temperature': 0
            },
            timeout=25
        )
        if r.status_code == 200:
            content = r.json()['choices'][0]['message']['content']
            print(f"OK -> {content[:100]}")
            working.append(model)
        else:
            err = r.json().get('error', {}).get('message', '')[:100]
            print(f"FAIL {r.status_code}: {err}")
    except Exception as e:
        print(f"ERROR: {str(e)[:80]}")
    time.sleep(3)

print("\n=== WORKING MODELS ===")
for m in working:
    print(f"  {m}")
if not working:
    print("  None available right now — try again in a few minutes.")
