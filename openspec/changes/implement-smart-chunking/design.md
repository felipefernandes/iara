# Architectural Design: Smart Regex Chunking

## Component Overview
O componente `CodeChunker` localizado em `iara/memory/indexer.py` ganhará capacidades multi-idioma de forma incremental através de casamento de padrões Regex e balanço de chaves `{ }`.

### 1. Extensão do `CodeChunker`
A função principal `chunk_file` agora delegará para os seguintes tratadores com base na extensão do arquivo:
- `.py` -> `_chunk_python(self, file_path, content)`
- `.js`, `.ts` -> `_chunk_js_ts(self, file_path, content)`
- `.cs` -> `_chunk_csharp(self, file_path, content)`
- Outros -> `_chunk_text(self, file_path, content)`

### 2. Regexes de Declaração (JavaScript / TypeScript / C#)
O sistema usará listas de Regex compiladas estáticas para identificar declarações de funções e classes.
- JS/TS: `r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)'`, `r'^(?:export\s+)?class\s+(\w+)'`, `r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\('`
- C#: `r'(?:public|private|protected|internal|abstract|sealed)?\s*(?:static\s+)?(?:class|struct|interface|record|enum)\s+(\w+)'`, `r'(?:public|private|protected|internal)?\s*(?:static|virtual|override|abstract)?\s*[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{?'`

### 3. Extração de Blocos (Balanço de Chaves)
Em vez de parsear perfeitamente a AST, utilizaremos a estratégia mais leve possível: usaremos a *regex* para achar a abertura (assinatura de classe/função). Em seguida, contamos quantas `{` abrem e `}` fecham a partir da primeira chave até retornarmos a 0. Isso extrai o bloco certinho. Faremos isso iterativamente até processar o conteúdo do arquivo.

### 4. Vantagens e Trade-offs
A abordagem por regex/heurística não impõe dependências pesadas e preserva velocidade de O(N). Caso a sintaxe seja defeituosa ou extremamente caótica, a heurística de balanços fará *fallback* ou retornará recortes justos; suficiente para o LLM.
