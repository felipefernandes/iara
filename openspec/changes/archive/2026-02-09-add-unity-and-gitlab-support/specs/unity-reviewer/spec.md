## ADDED Requirements
### Requirement: Unity C# Analysis
The system SHALL support analyzing Unity C# code for specific performance and logic issues.

#### Scenario: Update Loop Optimization
- **WHEN** the system scans a C# script
- **AND** it detects a heavy operation (e.g., `GetComponent`, `Find`) inside an `Update`, `FixedUpdate`, or `LateUpdate` method
- **THEN** it MUST flag this as a Performance issue.

#### Scenario: Memory Management
- **WHEN** the system detects recurrent string concatenation or instantiation in loops
- **THEN** it MUST suggest using `StringBuilder` or Object Pooling.

### Requirement: Scanning Mode
The system SHALL support a file scanning mode to analyze codebases without git history.

#### Scenario: Scan Directory
- **WHEN** invoked with `--scan <directory>`
- **THEN** it MUST iterate through files matching the project's tech stack extensions (e.g., `.cs` for Unity) and analyze them.
