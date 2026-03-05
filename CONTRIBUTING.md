# Contributing to Iara / Contribuindo para Iara

🇺🇸 [English](#english) | 🇧🇷 [Português](#português)

---

## English

Thank you for your interest in contributing to Iara! This guide will help you get started.

### Development Setup

#### Prerequisites

- Python 3.11+
- pip
- git

#### Installation from Source

```bash
git clone https://github.com/felipefernandes/iara.git
cd iara
pip install -e .
```

For RAG features (optional):

```bash
pip install -e .[rag]
```

### Running Tests

Run the full test suite:

```bash
python -m unittest discover tests
```

### Code Coverage

Generate a coverage report:

```bash
python -m coverage run -m unittest discover tests
python -m coverage report
python -m coverage xml  # For CI/CD
```

### Project Structure

```
iara/
├── iara/              # Core package
│   ├── cli.py         # CLI interface
│   ├── reviewer.py    # Main review logic
│   ├── prompt.py      # Prompt generation
│   ├── config.py      # Configuration management
│   ├── models.py      # LLM provider integrations
│   ├── memory/        # RAG memory system
│   ├── platforms/     # CI platform adapters (GitHub, GitLab)
│   ├── parsers/       # Output parsers (inline, diff compression)
│   └── extensions/    # Rule-based extensions
├── tests/             # Test suite (unittest framework)
├── docs/              # Documentation
├── examples/          # Configuration examples
├── openspec/          # Formal specifications and proposals
└── .github/workflows/ # CI/CD automation
```

### Development Workflow

#### Branching Strategy (GitFlow)

- `main` - Production-ready code
- `feature/*` - New features (e.g., `feature/issue-45-smart-chunking`)
- `fix/*` - Bug fixes (e.g., `fix/issue-23-memory-leak`)
- `docs/*` - Documentation updates

#### Making Changes

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes and test:**

```bash
python -m unittest discover tests
```

3. **Commit with descriptive messages:**

```bash
git commit -m "feat: add smart chunking for JavaScript"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `chore:` - Maintenance tasks
- `test:` - Test additions or changes

4. **Push and open a Pull Request:**

```bash
git push origin feature/your-feature-name
```

### OpenSpec Proposal Process

For major changes (new capabilities, breaking changes, architecture shifts), use the OpenSpec system:

1. **Review existing specs:**

```bash
# List all specifications
ls openspec/specs/

# Check existing change proposals
ls openspec/changes/
```

2. **Create a proposal** - Follow the guidelines in `openspec/AGENTS.md`

3. **Wait for review and approval**

4. **Implement according to the approved design**

### Pull Request Guidelines

- **Write clear, descriptive PR titles** - Use conventional commits format
- **Reference issue numbers** - e.g., "Fixes #62" or "Closes #45"
- **Include test coverage** - All new features must have tests
- **Update documentation** - README, docs/, CHANGELOG as needed
- **Ensure CI checks pass** - All tests must pass, maintain coverage

### Code Quality Standards

- **Python 3.8+ compatibility** - Support Python 3.8-3.13
- **Use unittest framework** - Not pytest
- **Mock external API calls** - Use `unittest.mock`
- **Follow existing patterns** - Check similar code for consistency
- **Keep it simple** - Prefer clarity over cleverness

### Release Process

Releases follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (x.0.0) - Breaking changes
- **MINOR** (1.x.0) - New features (backward compatible)
- **PATCH** (1.0.x) - Bug fixes

Releases are automated:
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Create a git tag: `git tag -a v1.8.0 -m "Release v1.8.0"`
4. Push the tag: `git push origin v1.8.0`
5. GitHub Actions will automatically publish to PyPI

### Getting Help

- 📚 [Documentation](docs/) - Configuration and CI/CD guides
- 💬 [GitHub Discussions](https://github.com/felipefernandes/iara/discussions) - Ask questions
- 🐛 [GitHub Issues](https://github.com/felipefernandes/iara/issues) - Report bugs or request features

---

## Português

Obrigado pelo interesse em contribuir com o Iara! Este guia vai te ajudar a começar.

### Configuração de Desenvolvimento

#### Pré-requisitos

- Python 3.11+
- pip
- git

#### Instalação a partir do código-fonte

```bash
git clone https://github.com/felipefernandes/iara.git
cd iara
pip install -e .
```

Para funcionalidades RAG (opcional):

```bash
pip install -e .[rag]
```

### Executando Testes

Execute a suite completa de testes:

```bash
python -m unittest discover tests
```

### Cobertura de Código

Gere um relatório de cobertura:

```bash
python -m coverage run -m unittest discover tests
python -m coverage report
python -m coverage xml  # Para CI/CD
```

### Estrutura do Projeto

```
iara/
├── iara/              # Pacote principal
│   ├── cli.py         # Interface CLI
│   ├── reviewer.py    # Lógica principal de review
│   ├── prompt.py      # Geração de prompts
│   ├── config.py      # Gerenciamento de configuração
│   ├── models.py      # Integrações com provedores LLM
│   ├── memory/        # Sistema de memória RAG
│   ├── platforms/     # Adaptadores de plataforma CI (GitHub, GitLab)
│   ├── parsers/       # Parsers de saída (inline, compressão de diff)
│   └── extensions/    # Extensões baseadas em regras
├── tests/             # Suite de testes (framework unittest)
├── docs/              # Documentação
├── examples/          # Exemplos de configuração
├── openspec/          # Especificações formais e propostas
└── .github/workflows/ # Automação CI/CD
```

### Fluxo de Desenvolvimento

#### Estratégia de Branches (GitFlow)

- `main` - Código pronto para produção
- `feature/*` - Novas funcionalidades (ex: `feature/issue-45-smart-chunking`)
- `fix/*` - Correções de bugs (ex: `fix/issue-23-memory-leak`)
- `docs/*` - Atualizações de documentação

#### Fazendo Alterações

1. **Crie um branch de feature:**

```bash
git checkout -b feature/nome-da-sua-feature
```

2. **Faça suas mudanças e teste:**

```bash
python -m unittest discover tests
```

3. **Faça commit com mensagens descritivas:**

```bash
git commit -m "feat: adiciona smart chunking para JavaScript"
```

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - Novas funcionalidades
- `fix:` - Correções de bugs
- `docs:` - Mudanças na documentação
- `chore:` - Tarefas de manutenção
- `test:` - Adições ou mudanças em testes

4. **Envie e abra um Pull Request:**

```bash
git push origin feature/nome-da-sua-feature
```

### Processo OpenSpec

Para mudanças maiores (novas capacidades, breaking changes, mudanças arquiteturais), use o sistema OpenSpec:

1. **Revise as specs existentes:**

```bash
# Liste todas as especificações
ls openspec/specs/

# Verifique propostas de mudança existentes
ls openspec/changes/
```

2. **Crie uma proposta** - Siga as diretrizes em `openspec/AGENTS.md`

3. **Aguarde revisão e aprovação**

4. **Implemente de acordo com o design aprovado**

### Diretrizes para Pull Requests

- **Escreva títulos claros e descritivos** - Use formato de conventional commits
- **Referencie números de issues** - ex: "Fixes #62" ou "Closes #45"
- **Inclua cobertura de testes** - Todas as novas features devem ter testes
- **Atualize a documentação** - README, docs/, CHANGELOG conforme necessário
- **Garanta que os checks de CI passem** - Todos os testes devem passar, mantenha a cobertura

### Padrões de Qualidade de Código

- **Compatibilidade Python 3.8+** - Suporte Python 3.8-3.13
- **Use framework unittest** - Não pytest
- **Mock chamadas de API externas** - Use `unittest.mock`
- **Siga padrões existentes** - Verifique código similar para consistência
- **Mantenha simples** - Prefira clareza sobre complexidade

### Processo de Release

Releases seguem [Semantic Versioning](https://semver.org/):

- **MAJOR** (x.0.0) - Breaking changes
- **MINOR** (1.x.0) - Novas funcionalidades (compatível)
- **PATCH** (1.0.x) - Correções de bugs

Releases são automatizados:
1. Atualize versão em `pyproject.toml`
2. Atualize `CHANGELOG.md` com as mudanças
3. Crie uma tag git: `git tag -a v1.8.0 -m "Release v1.8.0"`
4. Envie a tag: `git push origin v1.8.0`
5. GitHub Actions irá automaticamente publicar no PyPI

### Obtendo Ajuda

- 📚 [Documentação](docs/) - Guias de configuração e CI/CD
- 💬 [GitHub Discussions](https://github.com/felipefernandes/iara/discussions) - Faça perguntas
- 🐛 [GitHub Issues](https://github.com/felipefernandes/iara/issues) - Reporte bugs ou solicite features

---

**Thank you for contributing! / Obrigado por contribuir!** 🎉
