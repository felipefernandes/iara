"""Model definitions and API constants."""

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Free models list — openrouter/free is the meta-router that auto-selects
# the best available free model, so it's the primary choice.
FREE_MODELS = [
    "openrouter/free",                                # Meta-router (auto-selects best free model)
    "nvidia/nemotron-3-nano-30b-a3b:free",            # NVIDIA Nemotron Nano 30B
    "stepfun/step-3.5-flash:free",                    # StepFun Step 3.5 Flash
]
