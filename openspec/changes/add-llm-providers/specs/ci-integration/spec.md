## ADDED Requirements
### Requirement: GitHub Action Provider Inputs
The system SHALL allow selecting the provider and supplying provider-specific API keys in the GitHub Action inputs.

#### Scenario: Default provider in GitHub Action
- **WHEN** the `provider` input is omitted
- **THEN** the action MUST default to `openrouter` and use `openrouter_api_key` if provided.

#### Scenario: OpenAI provider input
- **WHEN** the `provider` input is `openai` and `openai_api_key` is set
- **THEN** the action MUST export `OPENAI_API_KEY` and `IARA_PROVIDER=openai` before running Iara.
