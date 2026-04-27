# agent-orchestrator - Contexto minimo

Use este arquivo como primeiro contexto para OpenAI, Gemini, Codex ou outro agente.

## Projeto

`agent-orchestrator` e um orquestrador generico de agentes de IA com multiplos providers para repositorios locais.

## Objetivos

- Rotear tarefas entre providers.
- Controlar orcamento e uso de tokens.
- Manter memoria especifica por projeto fora do runtime central.
- Permanecer plug-and-play e reversivel.
- Operar com leitura por padrao nos repositorios-alvo.

## Estado atual

- Repo: `andreyoshimura/agent-orchestrator`
- Branch padrao: `main`
- Profiles por projeto: `projects/<project_id>/`
- Estado local: `var/state`
- Cache local: `var/cache`

## Comandos seguros principais

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Estrutura principal

- `app/core/`: runtime central e roteamento.
- `app/providers/`: adapters de providers.
- `app/agents/`: agentes locais.
- `app/storage/`: estado, cache e persistencia.
- `config/`: configuracoes de providers, rotas e limites.
- `projects/`: profiles e memoria por projeto.
- `scripts/`: entrypoints operacionais.
- `var/`: dados locais de execucao.

## Regras criticas

- Nao alterar runtime central sem escopo claro.
- Nao alterar roteamento ou limites sem decisao explicita.
- Nao ativar escrita em repositorios-alvo sem autorizacao explicita.
- Nao executar chamadas externas se a tarefa for apenas documental.
- Nao misturar memoria de projetos diferentes.

## Politica de contexto

Use o menor contexto suficiente para a tarefa.

Nao carregar por padrao:

- README completo
- `var/cache`
- `var/state` completo
- logs brutos
- arquivos locais sensiveis
