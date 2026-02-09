# model-provider Specification

## Purpose
TBD - created by archiving change generalize-iara. Update Purpose after archive.
## Requirements
### Requirement: Dynamic Model Selection
The system SHALL allow selecting a specific AI model via configuration or environment variables.

#### Scenario: Environment Variable Override
- **WHEN** `IARA_MODEL` environment variable is set (e.g., `google/gemini-1.5-pro`)
- **THEN** Iara MUST attempt to use ONLY that model, bypassing the default fallback list.
- **AND** if that model fails, it MUST report the error and stop (no fallback to free models if explicit model requested).

#### Scenario: Configured Preferred Model
- **WHEN** `model.preferred` is set in `.iara.json` AND `IARA_MODEL` is NOT set
- **THEN** Iara MUST attempt that model first.

### Requirement: Fallback Strategy control
The system SHALL allow enabling/disabling the fallback to free models.

#### Scenario: Disable Fallback
- **WHEN** `model.fallback_enabled` is set to `false`
- **THEN** Iara MUST NOT iterate through the default `FREE_MODELS` list if the primary model fails.

