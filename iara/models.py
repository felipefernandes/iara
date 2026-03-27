"""Model definitions and API constants."""

# Provider configurations
PROVIDER_CONFIGS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "auth_type": "bearer",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/felipefernandes/iara",
            "X-Title": "Iara Code Reviewer"
        }
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/chat/completions",
        "auth_type": "bearer",
        "extra_headers": {}
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "auth_type": "bearer",
        "extra_headers": {}
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/messages",
        "auth_type": "x-api-key",
        "extra_headers": {"anthropic-version": "2024-06-01"}
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
        "auth_type": "bearer",
        "extra_headers": {}
    }
}

SUGGESTED_MODELS = {
    "openrouter": ["openrouter/free", "anthropic/claude-opus-4-5", "openai/gpt-4o"],
    "openai": ["gpt-4o", "gpt-4.5-preview", "o1"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
    "anthropic": ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
}

# OpenRouter free models list — openrouter/free is the meta-router that auto-selects
# the best available free model, so it's the primary choice.
FREE_MODELS = [
    "openrouter/free",                                # Meta-router (auto-selects best free model)
    "nvidia/nemotron-3-nano-30b-a3b:free",            # NVIDIA Nemotron Nano 30B
    "stepfun/step-3.5-flash:free",                    # StepFun Step 3.5 Flash
]
