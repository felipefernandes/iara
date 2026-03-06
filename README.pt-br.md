# Iara - AI Code Reviewer 🧜‍♀️

![Iara - AI Code Review Agent](.assets/iara-github-banner.png)

🇺🇸 [Read in English](README.md)

Iara é uma ferramenta de revisão de código automatizada, agnóstica a projetos e configurável, projetada para rodar em pipelines de CI/CD ou localmente via CLI. Ela se conecta diretamente ao provedor de LLM de sua escolha — OpenRouter (modelos gratuitos), OpenAI, Google Gemini ou Anthropic Claude.

---

[![🧜‍♀️ Iara Code Review](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/iara-review.yml) [![🧪 Tests](https://github.com/felipefernandes/iara/actions/workflows/tests.yml/badge.svg)](https://github.com/felipefernandes/iara/actions/workflows/tests.yml) [![codecov](https://codecov.io/gh/felipefernandes/iara/branch/main/graph/badge.svg)](https://codecov.io/gh/felipefernandes/iara) [![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Iara%20Code%20Reviewer-blue?logo=github)](https://github.com/marketplace/actions/iara-code-reviewer) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Índice

- [Funcionalidades](#-funcionalidades)
- [Capacidades](#-capacidades)
- [Instalação e Setup](#-instalação-e-setup)
- [Como Usar](#-como-usar)
- [Privacidade & Segurança](#-privacidade--segurança)
- [Documentação](#-documentação)
- [Testes](#-testes)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 🚀 Funcionalidades

- **Agnóstica**: Configure o contexto do seu projeto (Tech Stack, Regras) via JSON.
- **Multi-Provedor**: Conecte diretamente ao OpenRouter, OpenAI, Google Gemini ou Anthropic Claude.
- **Fallback Inteligente**: Tenta modelos gratuitos automaticamente se o preferido falhar (apenas OpenRouter).
- **Rules-Based (Estático)**: Identifica padrões perigosos instantaneamente sem gastar tokens (ex: `GetComponent` em loops no Unity).
- **LLM-Based (Inteligente)**: Usa IA para entender a lógica, segurança e contexto, indo além da sintaxe.
- **GitHub + GitLab**: Integração nativa com ambas as plataformas, com comentários automáticos em PRs/MRs.
- **Reviews Multi-Idioma**: Configure o idioma de saída — reviews podem ser escritas em Português, Inglês, Espanhol, Francês e mais.

## 🧠 Capacidades

A Iara combina diferentes tipos de análise para uma revisão completa:

| Tipo | O que faz? | A Iara cobre? | Como? |
| :--- | :--- | :--- | :--- |
| **Análise Estática** | Caça bugs lendo o código (rápido). | ✅ **Sim** | Via Extensões (Regex) e LLM. |
| **Linting** | Corrige estilo e formatação. | ✅ **Sim** | LLM pode sugerir *Clean Code*. |
| **SAST** | Caça falhas de segurança no código. | ✅ **Sim** | Foco primário na busca por vulnerabilidades. |
| **Análise Dinâmica** | Caça bugs rodando o app (lento). | ❌ Não | Foco em CI/CD rápido (Code Review). |

### O que ela detecta?

1. **Unity / Game Dev**:
   - Uso de APIs lentas (`Find`, `GetComponent`) em loops críticos (`Update`).
   - Alocação excessiva de memória (Garbage Collection).
   - Excesso de logs (`Debug.Log`) em builds finais.

2. **Segurança (Geral)**:
   - Credenciais hardcoded (Senhas, API Keys).
   - Vulnerabilidades de Injeção (SQL, Command).
   - Falta de validação de inputs.

3. **Qualidade de Código**:
   - Lógica complexa ou confusa.
   - Erros de tratamento de exceções.
   - Sugestões de refatoração para legibilidade.

---

## 📦 Instalação e Setup

### 1. Instalar

```bash
pip install iara-reviewer
```

### 2. Configurar (Setup Interativo)

```bash
iara init
```

O wizard vai guiar você em **5 passos**:

1. **Idioma** — Escolha o idioma das reviews (en, pt-br, es, fr, etc.)
2. **Provedor** — Escolha seu provedor de LLM: `openrouter` (padrão, gratuito), `openai`, `gemini` ou `anthropic`
3. **API Key** — Informe a chave do provedor escolhido (validada e salva em `~/.iara/config.json`)
4. **Projeto** — Nome, tech stack, descrição
5. **Preferências** — Áreas de foco (Security, Performance, etc.)

Pronto! O config do projeto fica salvo em `.iara.json`.

### 3. Usar

```bash
git diff main | iara
```

### Verificar autenticação

```bash
iara auth status
```

### Setup manual (sem wizard)

Configure o provedor e sua chave via variáveis de ambiente:

```bash
# OpenRouter (padrão — modelos gratuitos disponíveis)
export OPENROUTER_API_KEY="sk-or-..."

# OpenAI
export IARA_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."

# Google Gemini
export IARA_PROVIDER="gemini"
export GEMINI_API_KEY="AIza..."

# Anthropic Claude
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
```

A prioridade de resolução da API key é: variável de ambiente > config global (`~/.iara/config.json`).

### Via clone (Desenvolvimento)

```bash
git clone https://github.com/felipefernandes/iara.git
cd iara
pip install -e .
```

---

## 🏃 Como Usar

### Via Pipe (Git Diff)

```bash
git diff main | iara
```

### Via Variável de Ambiente

```bash
export PR_DIFF=$(git diff main)
iara
```

### Modo Scan (Análise Estática)

```bash
iara --scan ./caminho/do/projeto
```

### Forçando Provedor e Modelo

```bash
# Anthropic Claude
export IARA_PROVIDER="anthropic"
export ANTHROPIC_API_KEY="sk-ant-..."
export IARA_MODEL="claude-sonnet-4-5-20250929"
git diff | iara

# OpenAI GPT-4o
export IARA_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export IARA_MODEL="gpt-4o"
git diff | iara

# Google Gemini
export IARA_PROVIDER="gemini"
export GEMINI_API_KEY="AIza..."
export IARA_MODEL="gemini-2.5-flash"
git diff | iara
```

---

## 🔒 Privacidade & Segurança

**Importante**: A Iara envia seu código para provedores de LLM de terceiros para análise. Embora conveniente, isso tem implicações de privacidade que você deve conhecer.

### O que acontece com seu código?
- Diffs de código são enviados para APIs externas (OpenRouter, OpenAI, Gemini, Anthropic, Groq)
- Provedores podem armazenar dados temporariamente para processamento
- Políticas de retenção e treinamento variam por provedor

### Comparação de Privacidade dos Provedores

| Provedor | Treina com dados da API | Retenção de Dados | Opções Enterprise | Melhor Para |
|----------|------------------------|-------------------|-------------------|-------------|
| **Anthropic** | ❌ Não | Temporário | ✅ Sim | Código sensível |
| **OpenAI** | ⚠️ Requer opt-out | 30 dias | ✅ Sim | Uso geral |
| **Gemini** | ⚠️ Varia | Não documentado | ✅ Sim | Uso geral |
| **Groq** | ⚠️ Não documentado | Não documentado | ❌ Não | Código público |
| **OpenRouter** | ⚠️ Depende do modelo | Varia | ❌ Não | Código público |

### Recomendações por Caso de Uso

- **Projetos Open Source**: Qualquer provedor (código já é público)
- **Projetos Privados (não-sensíveis)**: Anthropic ou Groq
- **Código Sensível/Proprietário**: Anthropic Enterprise ou LLM self-hosted
- **Indústrias Reguladas (HIPAA, PCI-DSS)**: Apenas LLM self-hosted (ex: Ollama - veja [Issue #76](https://github.com/felipefernandes/iara/issues/76))

Para informações detalhadas sobre privacidade e opções self-hosted, veja o **[Guia de Privacidade & Segurança](docs/privacy-security.md)** (em inglês).

---

## 📚 Documentação

Para guias detalhados e opções de configuração, veja:

- **[Guia de Configuração](docs/configuration.md)** - Configuração do projeto, provedores, modelos, memória RAG (em inglês)
- **[Integração CI/CD](docs/ci-integration.md)** - GitHub Actions, GitLab CI, Docker, comentários inline (em inglês)
- **[Guia de Privacidade & Segurança](docs/privacy-security.md)** - Privacidade de dados, políticas dos provedores, opções self-hosted (em inglês)
- **[Guia de Contribuição](CONTRIBUTING.md)** - Setup de desenvolvimento, testes, pull requests (bilíngue)

### Exemplos de Configuração

Exemplos completos de configuração estão disponíveis em [`examples/`](examples/):

- [`examples/iara-example.json`](examples/iara-example.json) - Configuração padrão
- [`examples/iara-example-inline.json`](examples/iara-example-inline.json) - Modo de comentários inline em PRs
- [`examples/github-workflow.yml`](examples/github-workflow.yml) - Workflow do GitHub Actions
- [`examples/gitlab-ci.yml`](examples/gitlab-ci.yml) - Pipeline do GitLab CI

### Links Rápidos

- [GitHub Marketplace](https://github.com/marketplace/actions/iara-code-reviewer) - Adicione Iara ao seu repositório
- [Pacote PyPI](https://pypi.org/project/iara-reviewer/) - Instale via pip
- [Changelog](CHANGELOG.md) - Histórico de versões e notas de release

---

## 🧪 Testes

```bash
python -m unittest discover tests
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja nosso [Guia de Contribuição](CONTRIBUTING.md) para:

- Setup de desenvolvimento
- Executando testes
- Padrões de qualidade de código
- Diretrizes para pull requests
- Processo de release

---

## 📜 Licença

MIT
