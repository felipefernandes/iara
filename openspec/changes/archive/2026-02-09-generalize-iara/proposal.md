# Change: Generalize Iara for Multi-Project and Multi-Model Support

## Why
Currently, Iara is tightly coupled to the "Curupira" project via hardcoded system prompts, context rules, and a fixed list of free OpenRouter models. Phase 1 of the roadmap requires Iara to be project-agnostic and configurable, allowing use in other projects (like Unity C# games) and supporting paid/high-performance models (GPT-4, Claude 3.5, Gemini 1.5 Pro) when needed.

## What Changes
- **Configuration System**: parsing of a configuration file (e.g., `.iara.json` or `pyproject.toml` section) to load project-specific context.
- **Dynamic Prompting**: `SYSTEM_PROMPT` will be constructed dynamically based on the configuration (Project Name, Rules, Tech Stack).
- **Model Selection**: Refactor of the model selection logic to allow specifying a preferred model provider/ID via configuration or environment variables, overriding the default "free model fallback" list if desired.
- **CLI/Env Support**: Support for `IARA_MODEL` and `IARA_CONFIG` environment variables.

## Impact
- **Affected Specs**: `configuration`, `model-provider` (New Specs).
- **Affected Code**: `ai-codereview.py` (Major refactor of `main`, `review_code`, and prompt definitions).
- **Breaking Changes**: None strictly, as we can default to Curupira settings if no config is found, preserving backward compatibility for the existing workflow, but the code structure will change significantly.
