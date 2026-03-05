# Proposal: Implementar Smart Chunking para JS, TS e C#

## Contexto e Problema
Atualmente, o `CodeChunker` do Iara faz chunking de código inteligentemente apenas para Python usando parsing da AST, extraindo classes e funções. Para outras linguagens (como JavaScript, TypeScript e C#), o sistema faz *fallback* para um chunking simples de texto (blocos de 100 linhas). Esse comportamento frequentemente corta funções no meio, gerando contextos fragmentados e ruidosos que prejudicam a qualidade da RAG (Retrieval-Augmented Generation) ao injetar o contexto no modelo de linguagem. 

## Solução Proposta
Este proposal endereça a Issue #45. A solução implementa métodos de extração de blocos baseados em expressões regulares (Regex) e heurísticas simples para JavaScript/TypeScript e C#. Isso dispensa a necessidade de parsers complexos para essas linguagens, mantendo o agente rápido e leve, mas resultando em chunks lógicos (funções/classes em sua integridade).

O fluxo será:
- `.js` e `.ts` serão processados por um novo método `_chunk_js_ts` (Regex para declarações de função, classes e arrow functions).
- `.cs` será processado por um novo método `_chunk_csharp` (Regex para classes e métodos com visibilidade public/private, etc).
- Arquivos de outras extensões seguirão usando fallback.

## Considerações
- Expressões regulares combinadas com rastreio de chaves `{}`, simulando parsing leve para obter com precisão as bordas do código, garantindo limits íntegros.
- Nenhuma nova dependência externa será requerida, seguindo o padrão minimalista (Diet Code).
