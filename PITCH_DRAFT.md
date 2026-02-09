# Proposta de Adoção: Iara Code Reviewer

**Assunto:** Apresentação da Iara - Nossa nova aliada no Code Review (Unity & Python)

Oi [Nome do Tech Lead],

Queria te mostrar uma ferramenta que desenvolvi para agilizar nosso processo de Code Review e garantir mais qualidade, especialmente nos projetos de Unity.

A **Iara** é um bot de revisão de código agnóstico que configurei para rodar tanto localmente quanto no nosso CI (GitLab).

**O que ela faz?**
1.  **Análise Estática para Unity**: Detecta automaticamente problemas de performance críticos (ex: `GetComponent` ou `Find` em `Update`, alocação de memória excessiva) antes mesmo de abrirmos o PR.
2.  **Review com IA**: Usa LLMs (Llama 3, Gemini) para analisar a lógica e segurança do código, sugerindo melhorias como um revisor humano faria.
3.  **Custo Zero/Baixo**: Configurei para usar modelos gratuitos via OpenRouter, mas é fácil plugar modelos mais robustos se precisarmos.
4.  **Integração CI/CD**: Já criei o template para rodar no GitLab CI a cada Merge Request.

**Para testar agora:**

Clone o repo e rode esse comando scan em qualquer projeto Unity nosso para ver o que ela encontra:

```bash
python ai-codereview.py --scan ./Assets/Scripts
```

A documentação completa está no `README.md`. Acho que isso pode salvar bastante tempo da equipe pegando erros triviais automaticamente.

O que acha de rodarmos um piloto em um dos projetos?

Abraço,
[Seu Nome]
