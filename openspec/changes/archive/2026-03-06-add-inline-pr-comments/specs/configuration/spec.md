# Capability: Configuration

## ADDED Requirements

### Requirement: CI Platform Configuration

Iara MUST support a `ci` section in `.iara.json` that specifies the CI platform and review mode for posting comments.

**Rationale**: Different CI platforms (GitHub, GitLab) have different APIs for inline comments. Explicit configuration ensures correct adapter is used and supports future platform additions.

#### Scenario: Parse ci.platform from config

**Given** a `.iara.json` file contains `{"ci": {"platform": "github"}}`
**When** Iara loads the configuration
**Then** Iara MUST extract `ci.platform` as `"github"`
**And** Iara MUST validate that platform is one of: `"github"`, `"gitlab"`
**And** Iara MUST raise a validation error if platform is not supported

#### Scenario: Parse ci.review_mode from config

**Given** a `.iara.json` file contains `{"ci": {"review_mode": "inline"}}`
**When** Iara loads the configuration
**Then** Iara MUST extract `ci.review_mode` as `"inline"`
**And** Iara MUST validate that review_mode is one of: `"summary"`, `"inline"`
**And** Iara MUST raise a validation error if review_mode is invalid

#### Scenario: Default values when ci section missing

**Given** a `.iara.json` file does NOT contain a `ci` section
**When** Iara loads the configuration
**Then** Iara MUST default `ci.platform` to `None` (no platform specified)
**And** Iara MUST default `ci.review_mode` to `"summary"`
**And** Iara MUST log an info message that inline mode is not configured

#### Scenario: Default review_mode when only platform specified

**Given** a `.iara.json` file contains `{"ci": {"platform": "github"}}`
**And** the `ci` section does NOT include `review_mode`
**When** Iara loads the configuration
**Then** Iara MUST default `ci.review_mode` to `"summary"`
**And** Iara MUST use the specified platform for summary comment posting

#### Scenario: Validation error for inline mode without platform

**Given** a `.iara.json` file contains `{"ci": {"review_mode": "inline"}}`
**And** the `ci` section does NOT include `platform`
**When** Iara loads the configuration
**Then** Iara MUST raise a validation error with message "inline mode requires ci.platform to be specified"
**And** Iara MUST NOT proceed with the review

### Requirement: Backward Compatibility

Iara MUST maintain backward compatibility with existing `.iara.json` configurations that do not include the `ci` section.

**Rationale**: Existing users should experience no behavior change when upgrading. Inline mode is opt-in.

#### Scenario: Existing config without ci section works as before

**Given** a `.iara.json` file with only `project`, `review`, `model` sections
**And** the file does NOT contain a `ci` section
**When** Iara runs a code review
**Then** Iara MUST behave identically to previous versions
**And** Iara MUST post a single summary comment (default behavior)
**And** Iara MUST NOT log any warnings about missing ci configuration

#### Scenario: Empty ci section uses defaults

**Given** a `.iara.json` file contains `{"ci": {}}`
**When** Iara loads the configuration
**Then** Iara MUST use default values: `platform=None`, `review_mode="summary"`
**And** Iara MUST NOT raise any validation errors
**And** Iara MUST function in summary mode

## MODIFIED Requirements

*No modifications to existing configuration requirements. This is purely additive.*
