"""Definicoes de modelos e constantes da API."""

# Configuracao da API OpenRouter
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Lista simplificada de modelos gratuitos e meta-modelos
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",         # Modelo experimental rapido e gratuito
    "google/gemini-2.0-pro-exp-02-05:free",      # Modelo Pro experimental
    "meta-llama/llama-3.2-3b-instruct:free",     # Llama 3.2 (leve e rapido)
    "microsoft/phi-3-mini-128k-instruct:free",   # Phi-3 (backup)
    "openrouter/free"                             # Meta-modelo como ultima opcao
]
