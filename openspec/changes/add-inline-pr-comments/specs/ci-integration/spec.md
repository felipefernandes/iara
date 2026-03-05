# Capability: CI Integration

## ADDED Requirements

### Requirement: Inline PR Comment Support

Iara MUST support posting inline comments on specific lines of code in pull requests when configured in inline review mode, for supported CI platforms (GitHub, GitLab).

**Rationale**: Inline comments provide better developer experience by anchoring feedback directly to the relevant code, matching industry standards set by CodeClimate, SonarCloud, and human reviewers.

#### Scenario: Post inline comments on GitHub PR

**Given** Iara is configured with `ci.platform: "github"` and `ci.review_mode: "inline"`
**And** the GitHub token has `pull-requests: write` permission
**When** Iara reviews a pull request
**Then** Iara MUST parse the LLM response as JSON with comments array
**And** Iara MUST post comments via GitHub Pull Request Review Comments API
**And** each comment MUST be anchored to the specified file and line number

#### Scenario: Post inline comments on GitLab MR

**Given** Iara is configured with `ci.platform: "gitlab"` and `ci.review_mode: "inline"`
**And** the GitLab token has `api` scope
**When** Iara reviews a merge request
**Then** Iara MUST parse the LLM response as JSON with comments array
**And** Iara MUST post discussions via GitLab Merge Request Discussions API
**And** each discussion MUST be anchored to the specified file and line number

#### Scenario: Fallback to summary comment on JSON parse error

**Given** Iara is configured with `ci.review_mode: "inline"`
**When** the LLM returns invalid JSON or non-JSON response
**Then** Iara MUST log a warning about JSON validation failure
**And** Iara MUST fall back to posting a single summary comment
**And** the summary comment SHOULD include line numbers where possible

#### Scenario: Fallback to summary comment on API error

**Given** Iara is configured with `ci.review_mode: "inline"`
**When** the platform API returns an error (403, 404, 500, etc.)
**Then** Iara MUST log the API error with status code and message
**And** Iara MUST fall back to posting a single summary comment
**And** Iara SHOULD include an error note in the comment footer

#### Scenario: Unsupported platform defaults to summary mode

**Given** Iara is configured with `ci.platform: "bitbucket"` (unsupported)
**When** Iara attempts to post review comments
**Then** Iara MUST log a warning that inline mode is not supported for this platform
**And** Iara MUST automatically use summary comment mode
**And** Iara MUST post a single comment via the platform's standard API

### Requirement: Platform Adapter Architecture

Iara MUST provide a platform adapter interface that abstracts CI platform-specific API implementations for posting review comments.

**Rationale**: Supports multiple platforms (GitHub, GitLab, future: Bitbucket, Azure DevOps) with consistent internal interface while isolating platform-specific logic.

#### Scenario: GitHub adapter posts review comments

**Given** a GitHub adapter is instantiated with valid credentials
**When** `post_inline_comments()` is called with a list of comments
**Then** the adapter MUST format comments according to GitHub PR Review API schema
**And** the adapter MUST make a POST request to `/repos/{owner}/{repo}/pulls/{pr_number}/reviews`
**And** the adapter MUST include commit SHA, event type, and comments array
**And** the adapter MUST return True on success (2xx status) or False on failure

#### Scenario: GitLab adapter posts merge request discussions

**Given** a GitLab adapter is instantiated with valid credentials
**When** `post_inline_comments()` is called with a list of comments
**Then** the adapter MUST format each comment according to GitLab MR Discussions API schema
**And** the adapter MUST make POST requests to `/projects/{id}/merge_requests/{mr_iid}/discussions`
**And** the adapter MUST include position data (base_sha, head_sha, new_path, new_line)
**And** the adapter MUST return True if all discussions posted successfully, False otherwise

#### Scenario: Adapter factory returns correct implementation

**Given** a platform name string ("github" or "gitlab")
**When** `get_adapter(platform, token, repo, pr_id)` is called
**Then** the factory MUST return an instance of the corresponding adapter class
**And** the adapter instance MUST be properly initialized with credentials
**And** the factory MUST raise ValueError if platform is unsupported

## MODIFIED Requirements

### Requirement: Summary Comment Posting

Iara MUST post summary comments both as the default mode and as a fallback when inline posting fails.

**Change**: Extend to support both direct posting and fallback scenarios.

**Previous**: Iara posts a single summary comment on PRs.

**Now**: Iara MUST post a single summary comment when:
- `ci.review_mode` is `"summary"` (default), OR
- `ci.review_mode` is `"inline"` but inline posting failed (fallback)

#### Scenario: Post summary comment as primary mode

**Given** Iara is configured with `ci.review_mode: "summary"` OR no `ci` section exists
**When** Iara completes a code review
**Then** Iara MUST post the LLM response as a single comment
**And** Iara MUST use the platform's standard issue/PR comment API
**And** the comment MUST include the Iara footer with attribution link

#### Scenario: Post summary comment as fallback from inline mode

**Given** Iara is configured with `ci.review_mode: "inline"`
**And** inline comment posting failed (JSON error or API error)
**When** the fallback logic is triggered
**Then** Iara MUST post the review content as a single summary comment
**And** Iara SHOULD include a note explaining inline mode failed
**And** the fallback comment MUST still provide useful feedback to developers
