# Project Context

## Purpose
Iara is an automated AI code reviewer originally designed for the "Curupira" open-source project. Its goal is to provide intelligent, context-aware code reviews focusing on Logic, Security, and Performance. 
It follows the "Diet Code" manifesto (efficiency, simplicity) and is designed to run on constrained hardware (Raspberry Pi).
The project is evolving to be project-agnostic, supporting multiple LLM providers (Free & Paid) and integrating into CI/CD pipelines (GitLab/GitHub).

## Tech Stack
- **Language**: Python 3 (Standard Library preferred to minimize dependencies).
- **AI Provider**: OpenRouter API (initially), abstracting access to models like Gemini, Claude, Llama, and DeepSeek.
- **CI/CD**: GitHub Actions (current), GitLab CI (planned).
- **Target Runtime**: Lightweight environments (e.g., Raspberry Pi 3, 1GB RAM) and standard CI runners.

## Project Conventions

### Code Style
- Follow **PEP 8** guidelines.
- **Minimal Dependencies**: Avoid heavy libraries (pandas, numpy) unless absolutely necessary. Use `urllib` instead of `requests` where possible to save resources.
- **Type Hinting**: Use Python type hints for clarity.
- **Docstrings**: Required for all functions and classes (Google or NumPy style).

### Architecture Patterns
- **Agentic Design**: Structured as an agent (`Iara`) that uses "Skills" or extensions for specific tasks (e.g., Unity Reviewer, Python Reviewer).
- **Dependency Injection**: Context (config, connections) should be injected, not hardcoded.
- **Configuration**: Environment variables (`.env`) for secrets and runtime config.

### Testing Strategy
- **Unit Tests**: Required for core logic, parsers, and configuration loading. Use `unittest` or `pytest`.
- **Integration Tests**: Mocked API calls to verify OpenRouter integration without spending credits/quota.
- **Regression Testing**: Ensure new models/prompts doesn't degrade review quality.

### Git Workflow
- **Main Branch**: `main` is the source of truth.
- **Feature Branches**: `feat/` for new features, `fix/` for bugs.
- **Commit Messages**: Conventional Commits (e.g., `feat: add unity support`, `fix: token limit error`).

## Domain Context
- **Curupira Legacy**: The bot understands constraints of the "Curupira" project (IoT, RPi, Offline-first) but can be configured to ignore them for other projects.
- **Game Dev**: Support for Unity C# best practices (performance on mobile, memory management).

## Important Constraints
- **Hardware**: Must run on low-spec hardware (1 core, <1GB RAM availability).
- **Cost**: Default to free/low-cost models, but allow high-end models via config.
- **Latency**: Reviews should be reasonably fast, but quality > speed.

## External Dependencies
- **OpenRouter API**: Primary gateway for LLMs.
