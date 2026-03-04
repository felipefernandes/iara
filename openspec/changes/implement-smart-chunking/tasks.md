# Implementation Tasks

1. **Adicionar Regex Pattern e Helper Multi-idioma:** No arquivo `iara/memory/indexer.py`, criar construtos regex para JS/TS e C#, além de um método utilitário `_extract_brace_blocks(content, patterns)` que receba uma string de conteúdo do arquivo e encontre funções e classes, extraindo do match até o balanceamento final das chaves `{}`.
2. **Atualizar `CodeChunker.chunk_file`:** Modificar o método base para derivar para os novos tratadores dependendo da extensão do arquivo (`.js`, `.ts` invariavelmente vão para `_chunk_js_ts` e `.cs` para `_chunk_csharp`).
3. **Implementar `_chunk_js_ts`:** Utilizar a função auxiliar de extração para popular iterativamente objetos do tipo `CodeChunk` para classes e funções/métodos no Javascript e Typescript.
4. **Implementar `_chunk_csharp`:** Idemmente ao anterior, utilizar a extração com regex especificamente desenhado para C#.
5. **Escrever Testes JS/TS:** Em `tests/test_indexer.py`, providenciar conteúdo simulado de JS e TS, validando o número de pedaços extraídos contra a contagem correta das abordagens Regex.
6. **Escrever Testes C#:** Validar a extração correta baseada num código Unity de exemplo c# em `tests/test_indexer.py`.
7. **Atualizar Documentação:** Modificar o arquivo `README.md` relatando que o "chunking inteligente" suporta JS, TS e C#.
