"""Core code review logic with LLM integration."""

import os
import sys
import json
import re
import time
import urllib.request
import urllib.error

from iara.models import PROVIDER_CONFIGS, FREE_MODELS, SUGGESTED_MODELS
from iara.auth import normalize_provider, SUPPORTED_PROVIDERS
from iara.prompt import generate_system_prompt
from iara.diff_compressor import DiffCompressor

# Optional RAG imports
try:
    from iara.memory.lancedb_store import LanceDBMemory
    from iara.memory.retriever import Retriever
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def _extract_error_message(status_code: int, body: str, model: str) -> str:
    """Extract a user-friendly error message from an API error response."""
    try:
        data = json.loads(body)
        msg = data.get("error", {}).get("message", "")
    except (json.JSONDecodeError, AttributeError):
        msg = ""

    if status_code == 404:
        return "model not available"
    if status_code == 429:
        return "rate limited — will retry with next model"
    if status_code == 400 and "not a valid model" in msg.lower():
        return "model ID no longer valid"
    if status_code == 401:
        return "invalid API key"
    if msg:
        return msg
    return f"HTTP {status_code}"


def _build_headers(api_key: str, provider: str) -> dict:
    provider_cfg = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["openrouter"])
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Iara-Code-Reviewer/1.0"
    }

    if provider_cfg["auth_type"] == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        headers["x-api-key"] = api_key

    headers.update(provider_cfg["extra_headers"])
    return headers


def _build_payload(diff: str, model: str, system_prompt: str, provider: str) -> dict:
    user_content = f"Review the following code diff:\n\n```diff\n{diff}\n```"

    if provider == "anthropic":
        return {
            "model": model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
            "temperature": 0.3,
            "max_tokens": 6000,
        }

    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.3,
        "max_tokens": 6000,
    }


def _extract_content(result: dict, provider: str) -> str:
    if provider == "anthropic":
        content_blocks = result.get("content", [])
        if content_blocks and isinstance(content_blocks, list):
            text = content_blocks[0].get("text")
            if text:
                return text
        raise ValueError("API returned success but no 'content' text.")

    if "choices" in result and len(result["choices"]) > 0:
        content = result["choices"][0]["message"]["content"]
        if content is None:
            raise ValueError("API returned empty content.")
        return content

    raise ValueError("API returned success but no 'choices'.")


def review_code_with_model(diff: str, api_key: str, model: str, system_prompt: str, provider: str) -> str:
    """Try to review code with a specific model."""
    provider_cfg = PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS["openrouter"])
    payload = _build_payload(diff, model, system_prompt, provider)
    headers = _build_headers(api_key, provider)

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(provider_cfg["base_url"], data=data, headers=headers)

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "error" in result:
                raise Exception(f"API Error: {result['error']}")

            content = _extract_content(result, provider)

            # Strip <think> blocks (Common in DeepSeek R1)
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

            if not content:
                raise ValueError("Model returned empty content (or only <think> tags).")

            return content

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        # Extract friendly message from JSON error response
        friendly_msg = _extract_error_message(e.code, error_body, model)
        raise Exception(friendly_msg)


def review_code(diff: str, api_key: str, config: dict) -> str:
    """Execute code review trying configured model or fallback.

    Returns:
        Review text (markdown for summary mode, JSON string for inline mode)
    """
    if not diff.strip():
        return "✅ No code changes to review."

    # Compress diff if necessary
    max_diff_tokens = config.get("review", {}).get("max_diff_tokens", 12000)
    try:
        compressor = DiffCompressor(max_diff_tokens=max_diff_tokens)
        diff = compressor.compress(diff)
    except ValueError as e:
        print(f"⚠️  Invalid max_diff_tokens config: {e}. Using default 12000.", file=sys.stderr)
        compressor = DiffCompressor(max_diff_tokens=12000)
        diff = compressor.compress(diff)

    # RAG: Retrieve context if available
    context_text = ""
    if RAG_AVAILABLE:
        try:
            # TODO: Make persistence path configurable
            memory = LanceDBMemory()
            retriever = Retriever(memory)
            # Retrieve up to 3 chunks to keep prompt size manageable
            context_text = retriever.retrieve_context_for_diff(diff, max_chunks=3)
            if context_text:
                print("🧠 Context retrieved from memory.", file=sys.stderr)
        except Exception as e:
            # Fail silently on RAG errors to not break the review
            print(f"⚠️ RAG Error: {e}", file=sys.stderr)

    # Get review mode from config
    review_mode = config.get("ci", {}).get("review_mode", "summary")

    system_prompt = generate_system_prompt(config, review_mode=review_mode)

    if context_text:
        system_prompt += f"\n\n{context_text}"

    # Determine which model to use
    model_config = config.get("model", {})
    preferred_model = os.environ.get("IARA_MODEL") or model_config.get("preferred")
    provider = model_config.get("provider", "openrouter")
    provider = normalize_provider(provider)
    if not provider:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        return "❌ Invalid provider configured. Supported providers: %s" % supported
    fallback_enabled = model_config.get("fallback_enabled", True)

    models_to_try = []

    if preferred_model:
        models_to_try.append(preferred_model)

    if (fallback_enabled or not preferred_model) and provider == "openrouter":
        for m in FREE_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

    # If IARA_MODEL env var is set: use ONLY that model
    env_model = os.environ.get("IARA_MODEL")
    if env_model:
        models_to_try = [env_model]

    if not models_to_try:
        # Fall back to the first suggested model for this provider
        default_models = SUGGESTED_MODELS.get(provider, [])
        if default_models:
            models_to_try = [default_models[0]]
        else:
            return (
                "❌ No model configured for provider '%s'. "
                "Set IARA_MODEL or model.preferred in .iara.json."
            ) % provider

    errors = []
    total = len(models_to_try)

    print(f"🔄 Starting review with {total} model(s)...", file=sys.stderr)

    for i, model in enumerate(models_to_try, 1):
        try:
            print(f"🔄 [{i}/{total}] Trying {model}...", file=sys.stderr)
            result = review_code_with_model(diff, api_key, model, system_prompt, provider)
            print(f"✅ Review completed with {model}.", file=sys.stderr)
            return result
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            error_msg = str(e)
            print(f"   ⏭️  {model} — {error_msg}", file=sys.stderr)
            errors.append(f"{model}: {error_msg}")
            time.sleep(1)
        except Exception as e:
            error_msg = str(e)
            print(f"   ⏭️  {model} — {error_msg}", file=sys.stderr)
            errors.append(f"{model}: {error_msg}")
            time.sleep(1)

            if env_model:
                break

    print("❌ All models failed.", file=sys.stderr)
    return f"❌ Could not review with any available model.\nErrors:\n" + "\n".join(errors)
