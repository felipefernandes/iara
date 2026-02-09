# Design: Generalize Iara Configuration

## Context
Iara needs to move from a single-file script with hardcoded values to a configurable tool that can adapt to different projects (Python, Unity C#, etc.) and budget constraints (Free vs Paid models).

## Decisions

### 1. Configuration File Format
We will use **JSON** (`.iara.json`) for the primary configuration because Python has built-in support (no extra dependencies like `toml` or `yaml` required, adhering to the "Minimal Dependencies" convention in `project.md`).

**Schema Draft:**
```json
{
  "project": {
    "name": "Project Name",
    "description": "Short description...",
    "tech_stack": ["Python", "Unity"]
  },
  "review": {
    "focus_areas": ["Security", "Performance", "Logic"],
    "ignore_patterns": ["*.meta", "tests/*"]
  },
  "model": {
    "provider": "openrouter",
    "preferred": "google/gemini-2.0-flash-exp:free",
    "fallback_enabled": true
  }
}
```

### 2. Prompt Construction
The System Prompt will be a template populated by the config.

**Template Structure:**
1. **Identity**: "Você é Iara, revisora do projeto {project.name}..."
2. **Context**: "{project.description}"
3. **Rules**: Derived from `tech_stack` and `focus_areas`.
    - If "Unity" in tech_stack -> Add Unity-specific best practices.
    - If "Python" -> Add PEP8 and performance tips.
4. **Format**: Standard output format (already defined, but can be customized).

### 3. Model Logic Refactor
Current logic: `Iterate FREE_MODELS list -> Return first success`.
New logic:
1. Check `ENV["IARA_MODEL"]`. If set, try that model ONLY.
2. Check `config.model.preferred`. If set, try that.
3. If fail and `fallback_enabled` is true (or default), iterate through `FREE_MODELS` (legacy list) or a configured list.

## alternatives Considered
- **TOML/YAML**: Rejected to keep `ai-codereview.py` dependency-free (standard library only).
- **Hardcoded Profiles**: Rejected because it doesn't scale to user-defined projects.

## Risks
- **Complexity**: The script will grow in size. We might need to split it into modules eventually, but for now, we will keep it single-file for portability (as per `project.md` runtime constraints), using a class-based structure if needed (e.g., `IaraConfig`, `ModelEngine`).
