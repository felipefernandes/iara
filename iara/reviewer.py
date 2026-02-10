"""Core code review logic with LLM integration."""

import os
import sys
import json
import re
import time
import urllib.request
import urllib.error

from iara.models import OPENROUTER_API_URL, FREE_MODELS
from iara.prompt import generate_system_prompt


def review_code_with_model(diff: str, api_key: str, model: str, system_prompt: str) -> str:
    """Try to review code with a specific model."""
    max_chars = 15000
    if len(diff) > max_chars:
        diff = diff[:max_chars] + "\n\n[... diff truncated due to size limit ...]"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review the following code diff:\n\n```diff\n{diff}\n```"}
        ],
        "temperature": 0.3,
        "max_tokens": 6000,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/felipefernandes/iara",
        "X-Title": "Iara Code Reviewer"
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OPENROUTER_API_URL, data=data, headers=headers)

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "error" in result:
                 raise Exception(f"API Error: {result['error']}")

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]

                # Strip <think> blocks (Common in DeepSeek R1)
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

                if not content:
                    raise ValueError("Model returned empty content (or only <think> tags).")

                return content
            else:
                raise ValueError("API returned success but no 'choices'.")

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP Error {e.code}: {error_body}")


def review_code(diff: str, api_key: str, config: dict) -> str:
    """Execute code review trying configured model or fallback."""
    if not diff.strip():
        return "✅ No code changes to review."

    system_prompt = generate_system_prompt(config)

    # Determine which model to use
    preferred_model = os.environ.get("IARA_MODEL") or config.get("model", {}).get("preferred")
    fallback_enabled = config.get("model", {}).get("fallback_enabled", True)

    models_to_try = []

    if preferred_model:
        models_to_try.append(preferred_model)

    if fallback_enabled or not preferred_model:
        for m in FREE_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

    # If IARA_MODEL env var is set: use ONLY that model
    env_model = os.environ.get("IARA_MODEL")
    if env_model:
        models_to_try = [env_model]

    errors = []

    print(f"🔄 Starting review. Model queue: {models_to_try}", file=sys.stderr)

    for model in models_to_try:
        try:
            print(f"🔄 Trying model: {model}...", file=sys.stderr)
            return review_code_with_model(diff, api_key, model, system_prompt)
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            error_msg = str(e)
            print(f"⚠️ Connection/HTTP error on model {model}: {error_msg}", file=sys.stderr)
            errors.append(f"{model}: {error_msg}")
            time.sleep(1)
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Unexpected error on model {model}: {error_msg}", file=sys.stderr)
            errors.append(f"{model}: {error_msg}")
            time.sleep(1)

            if env_model:
                break

    return f"❌ Could not review with any available model.\nErrors:\n" + "\n".join(errors)
