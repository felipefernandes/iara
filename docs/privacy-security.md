# Privacy & Security Guide 🔒

This guide provides transparent information about data privacy and security when using Iara Code Reviewer.

---

## Overview

**Important**: Iara is designed to send code diffs to third-party LLM provider APIs for analysis. While this enables powerful AI-based code reviews, it has privacy and security implications you should understand before use.

---

## How Iara Handles Your Code

### Data Flow

```
Your Repository
    ↓
Iara CLI/Bot (reads git diff)
    ↓
HTTP Request (TLS encrypted)
    ↓
LLM Provider API (OpenRouter, OpenAI, Gemini, Anthropic, Groq)
    ↓
LLM processes code and generates review
    ↓
Response back to Iara
    ↓
Review posted as PR comment or displayed in terminal
```

### What Gets Sent

- **Code diffs**: Changed lines of code from your commits/PRs
- **Context**: File paths, line numbers
- **Configuration**: Project description, tech stack (from `.iara.json`)
- **Prompt**: System instructions for the LLM

### What Does NOT Get Sent

- ❌ Full repository contents (only diffs)
- ❌ Git history or commit messages
- ❌ Environment variables or secrets (unless in the diff itself)
- ❌ Binary files or assets

---

## Privacy Risks

### 1. Data Exposure
Your code is sent to third-party servers. Even with TLS encryption, the provider can read your code in plain text.

### 2. Data Retention
Providers may store API requests for debugging, compliance, or service improvement. Retention periods vary.

### 3. Training Data
Some providers may use API data to train or improve their models, unless explicitly opted out.

### 4. Compliance Violations
If your code contains regulated data (PII, PHI, PCI), sending it to external APIs may violate GDPR, HIPAA, PCI-DSS, or other regulations.

### 5. Accidental Leaks
If your diff contains secrets (API keys, passwords), they will be sent to the provider.

---

## Provider Privacy Policies

### Anthropic Claude
- **Training on API data**: ❌ **No** - [Explicit policy](https://www.anthropic.com/legal/commercial-terms) states API data is not used for training
- **Data retention**: Temporary (deleted after processing, except for trust & safety monitoring)
- **Compliance**: SOC 2 Type II, GDPR, HIPAA (BAA available)
- **Best for**: Sensitive/proprietary code

### OpenAI (GPT)
- **Training on API data**: ⚠️ **Opt-out required** - By default, API data is not used for training, but you must explicitly opt out
- **Data retention**: 30 days for abuse monitoring
- **Compliance**: SOC 2, GDPR, HIPAA (BAA available for Enterprise)
- **Best for**: General use with Enterprise API

### Google Gemini
- **Training on API data**: ⚠️ **Varies** - API policies differ from consumer products; not clearly documented
- **Data retention**: Not clearly documented
- **Compliance**: GDPR, ISO 27001
- **Best for**: General use, non-sensitive code

### Groq
- **Training on API data**: ⚠️ **Not documented** - Privacy policy unclear
- **Data retention**: Not clearly documented
- **Compliance**: Not clearly documented
- **Best for**: Public/open-source code only

### OpenRouter
- **Training on API data**: ⚠️ **Depends on underlying model** - OpenRouter is a proxy; policies vary by model
- **Data retention**: Varies by model
- **Compliance**: No enterprise agreements
- **Best for**: Public/open-source code, experimentation

---

## Recommendations by Scenario

### Open Source Projects ✅
**Risk Level**: Low (code is already public)

**Recommended Providers**: Any (OpenRouter free models, Groq, Anthropic)

### Private Projects (Non-Sensitive) ⚠️
**Risk Level**: Medium

**Recommended Providers**:
- **Anthropic Claude** (best privacy guarantees)
- **Groq** (fast, but weaker privacy policies)
- **OpenAI** (with opt-out enabled)

### Sensitive/Proprietary Code 🔐
**Risk Level**: High

**Recommended Approach**:
1. **Anthropic Enterprise** with BAA (Business Associate Agreement)
2. **OpenAI Enterprise** with data processing addendum
3. **Self-hosted LLM** (Ollama, LM Studio) - see [Issue #76](https://github.com/felipefernandes/iara/issues/76)

**Do NOT use**: OpenRouter, Groq, or free models

### Regulated Industries (HIPAA, PCI-DSS, FedRAMP) 🏥💳
**Risk Level**: Critical

**Required**: Self-hosted LLM only (e.g., Ollama with CodeLlama)

Using external APIs for regulated code is likely **non-compliant** and could result in:
- Regulatory fines
- Breach notifications
- Loss of certifications

---

## Mitigation Strategies

### 1. Use Privacy-Focused Providers
Choose providers with clear privacy policies and compliance certifications.

**Example**:
```bash
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Filter Sensitive Diffs
Review diffs before sending them to Iara. Exclude files containing:
- Customer data (PII, PHI)
- Credentials or API keys
- Business-critical algorithms

**Example** (`.gitignore`-like patterns):
```json
{
  "review": {
    "ignore_patterns": [
      "**/secrets.json",
      "**/*.env",
      "**/credentials/**",
      "**/config/production.yaml"
    ]
  }
}
```

### 3. Self-Hosted LLM (Coming Soon)
Run Iara with a local LLM (Ollama) to keep all data on your infrastructure.

**Benefits**:
- ✅ Zero data leakage
- ✅ Full compliance (GDPR, HIPAA, PCI)
- ✅ No API costs
- ✅ Works offline

**Track Progress**: [Issue #76 - Add Ollama support](https://github.com/felipefernandes/iara/issues/76)

### 4. Enterprise Agreements
For large organizations, negotiate BAAs or DPAs (Data Processing Agreements) with providers.

**Providers offering enterprise agreements**:
- Anthropic (BAA for HIPAA)
- OpenAI (DPA for GDPR, BAA for HIPAA)
- Google (DPA for GDPR)

### 5. Secrets Scanning
Use pre-commit hooks to prevent secrets from entering diffs:
- [git-secrets](https://github.com/awslabs/git-secrets)
- [detect-secrets](https://github.com/Yelp/detect-secrets)
- [gitleaks](https://github.com/gitleaks/gitleaks)

---

## FAQ

### Q: Can I use Iara for open-source projects?
**A**: Yes! Since the code is already public, there's minimal additional risk.

### Q: Is Iara GDPR compliant?
**A**: Iara itself doesn't store data, but the LLM providers you use must be GDPR compliant. Anthropic, OpenAI, and Gemini support GDPR.

### Q: Can I use Iara for code containing PII?
**A**: Not recommended unless you use a self-hosted LLM or enterprise provider with a BAA.

### Q: What if my diff accidentally contains a secret?
**A**: Revoke the secret immediately. It was sent to the provider's API and may be logged. Use tools like `git-secrets` to prevent this.

### Q: Does Iara store my code?
**A**: No. Iara is stateless (except for optional RAG memory, which is local). Only LLM providers may store data.

### Q: Can I audit what data is sent?
**A**: Yes. Run Iara with `--verbose` or inspect network traffic. All requests go to well-known API endpoints.

### Q: When will self-hosted LLM support be available?
**A**: We're tracking this in [Issue #76](https://github.com/felipefernandes/iara/issues/76). Implementation timeline depends on community interest.

---

## Best Practices

1. **Know your data**: Understand what's in your diffs before running reviews
2. **Choose appropriate providers**: Match provider privacy policies to your risk tolerance
3. **Use ignore patterns**: Exclude sensitive files from reviews
4. **Rotate secrets**: If secrets are exposed, revoke them immediately
5. **Educate your team**: Ensure developers understand privacy implications
6. **Review provider terms**: Read and understand privacy policies before use
7. **Consider self-hosting**: For maximum security, use local LLMs (coming soon)

---

## Transparency Statement

We believe in **radical transparency** about data privacy. This document aims to give you all the information needed to make informed decisions about using Iara in your projects.

If you find inaccuracies or have questions, please [open an issue](https://github.com/felipefernandes/iara/issues) or [contact us](https://github.com/felipefernandes/iara/discussions).

---

## Related Resources

- [Anthropic Privacy Policy](https://www.anthropic.com/legal/privacy)
- [OpenAI API Data Usage](https://openai.com/policies/api-data-usage-policies)
- [Google Gemini Privacy](https://ai.google.dev/gemini-api/terms)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Issue #76: Ollama Support](https://github.com/felipefernandes/iara/issues/76)

---

**Last Updated**: 2026-03-06
**Version**: 1.8.0
