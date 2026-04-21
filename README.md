# agent-orchestrator

Orquestrador genérico de IA e agentes com múltiplos providers para repositórios locais.

## Objetivos

- Rotear tarefas entre múltiplos providers de IA
- Controlar orçamento e uso de tokens
- Manter a memória específica de cada projeto fora do runtime central
- Permanecer plug-and-play e reversível
- Usar acesso somente leitura por padrão nos repositórios-alvo

## Princípios de design

- Somente leitura por padrão
- Sem conversa livre entre providers
- O orchestrator é o único componente autorizado a repassar resumos estruturados entre agentes
- O caminho do repositório-alvo é configurado externamente
- O fallback entre providers é baseado em regras
- Prompts e memória específicos do projeto ficam em `projects/<project_id>/`

## Política de execução

- As preferências e fallbacks de provider por tarefa ficam em `config/routing.yaml`
- O comportamento de retry e fallback também é configurado por tarefa em `routing.<task>.execution`
- O core mantém defaults seguros, mas a política específica de cada tarefa deve ser ajustada na configuração, não codificada diretamente no runtime

## Persistência operacional

- O resultado mais recente de cada tarefa por projeto é persistido em `var/state`
- Fingerprints resumidos de execução de tarefas são armazenados em cache em `var/cache`
- O uso diário de orçamento por provider é persistido em `var/state`
- Essa persistência é local e reversível; ela existe para reduzir trabalho manual repetido de inspeção entre execuções

## Papéis planejados dos providers

- **Claude free**: review local pequeno, análise de snippets, segunda opinião
- **Gemini**: análise ampla do repositório, mapeamento de dependências, planejamento de refactors maiores
- **OpenAI**: arbitragem, síntese, decisão final

## Tarefas iniciais

- `explain-file`
- `review-snippet`
- `review-diff`
- `map-dependencies`
- `summarize-module`
- `compare-options`
- `final-decision`

## Fluxo local

- `bash scripts/task.sh inspect-project` inspeciona o profile ativo do projeto e valida os arquivos associados
- `bash scripts/task.sh inspect-task <task-type> '<json>'` mostra uma prévia do roteamento, arquivos selecionados, plano local e disponibilidade dos providers para qualquer tarefa
- `bash scripts/task.sh inspect-budget` mostra o gasto diário atual e o orçamento restante por provider
- `bash scripts/task.sh diagnose-orchestrator` mostra diagnósticos de projeto, runtime, configuração e armazenamento
- `bash scripts/task.sh assemble-context <task-type> '<json>'` monta um contexto reutilizável de tarefa a partir de fontes globais e do projeto
- `bash scripts/task.sh list-python-files` lista os arquivos Python do repositório-alvo configurado
- `bash scripts/task.sh pick-python-file <query>` ranqueia arquivos Python por nome parcial
- `bash scripts/task.sh explain-best-python-match <query>` seleciona e mostra a prévia estrutural do melhor match Python
- `bash scripts/task.sh review-best-python-match <query>` seleciona e faz review do melhor match Python

## Estrutura do repositório

```text
agent-orchestrator/
  app/
    core/
    providers/
    agents/
    storage/
  config/
  projects/
    ia-trade/
      prompts/
      memory/
  scripts/
  var/
    logs/
    cache/
    state/
  .env.example
  README.md
```

## Defaults de segurança

- `AI_REPO_WRITE_ENABLED=false`
- o uso de providers é opcional e controlado por env/config
- o repositório do projeto é referenciado por caminho, não embutido neste repositório
- este repositório pode ser removido sem tocar no projeto-alvo

## Seleção de profile

- `AI_DEFAULT_PROJECT` seleciona o profile ativo do projeto
- `AI_PROJECTS_ROOT` pode apontar para um diretório alternativo de profiles ao validar múltiplos projetos localmente

## Próximo passo

Copie `.env.example` para `.env`, ajuste as chaves dos providers que deseja usar e configure `projects/ia-trade/project.yaml` com o caminho local do repositório-alvo.
