## ADDED Requirements
### Requirement: Language-Specific Smart Chunking
The indexer MUST use language-specific strategies (AST or regex) to chunk code accurately by logical boundaries (functions, classes) instead of falling back to raw line chunks prematurely.

#### Scenario: Python chunks using AST
- **Given** a `.py` file
- **When** the file is indexed
- **Then** it is chunked using Python's AST parser to extract functions and classes

#### Scenario: JavaScript and TypeScript chunks using Regex
- **Given** a `.js` or `.ts` file
- **When** the file is indexed
- **Then** it is chunked using Regex to extract functions, classes, and arrow functions
- **And** the chunks represent complete logical blocks rather than arbitrary lines

#### Scenario: C# chunks using Regex
- **Given** a `.cs` file
- **When** the file is indexed
- **Then** it is chunked using Regex to extract methods and classes
- **And** the chunks represent complete logical blocks

#### Scenario: Fallback chunking for unsupported languages
- **Given** a file with an unsupported extension (e.g., `.txt`, `.md`)
- **When** the file is indexed
- **Then** it falls back to a plain text chunking strategy of maximum 100 lines per chunk
