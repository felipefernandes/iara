# Proposal: make-indexer-ignore-patterns-configurable

## Goal
Tornar o campo `ignore_patterns` configurável no Indexer, lendo do arquivo `.iara.json`.

## Motivation
Atualmente, as pastas ignoradas durante a indexação do código base (RAG) estão definidas de forma hardcoded no `Indexer.__init__()`. Isso impede que usuários ignorem diretórios específicos de seus projetos (como pastas de fixtures, testes mockados, ou dados gerados) que não precisam de context review, desperdiçando tokens.
A solução é carregar a configuração de `review.ignore_patterns` do `.iara.json` e mesclá-la com o padrão já definido na classe `Indexer`.

## Impact
Dará aos usuários mais controle de quais arquivos o Iara deve processar, possivelmente reduzindo o escopo do codebase indexado e diminuindo o consumo de tokens/custos durante inferência.
