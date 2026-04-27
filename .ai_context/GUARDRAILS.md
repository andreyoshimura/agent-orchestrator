# agent-orchestrator - Guardrails

Use este arquivo como fonte central das regras de seguranca para agentes IA neste repositorio.

## Escopo obrigatorio

Antes de analisar ou alterar algo, declarar escopo:

- DOCS
- RUNTIME
- PROVIDERS
- ROUTING
- BUDGET
- PROJECT_PROFILE
- STORAGE
- SCRIPTS

Se o escopo nao estiver claro, parar e pedir delimitacao.

## Regras gerais

- Nao alterar runtime central sem objetivo e rollback claros.
- Nao alterar roteamento sem explicar impacto em fallback, custo e comportamento.
- Nao alterar limites de orcamento sem decisao explicita.
- Nao misturar memoria de projetos diferentes.
- Nao tratar cache ou state local como fonte absoluta da verdade.
- Nao ampliar acesso de escrita em repositorios-alvo sem autorizacao explicita.

## Providers

- Nao adicionar, remover ou priorizar provider sem registrar motivo.
- Nao assumir que todo provider esta disponivel.
- Sempre considerar fallback, timeout e budget headroom.
- Nao fazer chamada externa quando a tarefa for apenas documental ou estrutural.

## Configuracao

- Alteracoes em `config/` exigem justificativa curta.
- Separar mudanca de politica de roteamento de mudanca de runtime.
- Preferir configuracao a codigo quando a regra for operacional.

## Projetos alvo

- Profiles ficam em `projects/<project_id>/`.
- Memoria especifica de um projeto nao deve contaminar outro projeto.
- O caminho do repo alvo deve ser tratado como configuracao externa.

## Storage local

- `var/cache` pode ser descartavel.
- `var/state` e persistencia operacional local, mas pode estar desatualizado.
- Antes de concluir problema operacional, rodar healthcheck/diagnostico.

## Comandos seguros

Preferir:

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Nao fazer por padrao

- Nao fazer deploy.
- Nao executar automacao destrutiva.
- Nao apagar cache/state sem pedido explicito.
- Nao editar configuracao sensivel.
- Nao ativar escrita em repositorios-alvo sem pedido explicito.
- Nao rodar tarefas que chamem providers externos sem necessidade clara.
