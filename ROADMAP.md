# Roadmap de Desenvolvimento - Agent Orchestrator

**Última atualização**: 2026-05-20  
**Status**: MVP técnico funcional em hardening ativo  
**Testes**: 150 passando  
**Branch**: main

---

## 📋 Visão Geral

Roadmap estruturado com 8 etapas principais divididas em 4 fases. Cada etapa tem critérios de conclusão claros e é rastreável através do sistema de tarefas.

---

## 🎯 Fase 1: Hardening & Observabilidade (Próximas 2-3 semanas)

### #1 - Normalizar telemetria de uso (Claude, Gemini, OpenAI) ✅

**Prioridade**: 🔴 Alta  
**Status**: ✅ Completed (2026-05-20)  
**Deps**: Nenhuma  

Expandir telemetria de uso de provider além de OpenRouter. Implementar extração de métricas de uso para Claude, Gemini e OpenAI com formato consistente.

**Critérios de conclusão**:
- [x] Métricas de uso extraídas para os 3 provedores
- [x] Formato unificado em `provider_usage_metrics`
- [x] Testes cobrindo extração para cada provedor (7 novos testes)
- [x] `diagnose-orchestrator` mostra telemetria normalizada (via `operational_store`)

**Arquivos afetados**:
- `app/providers/claude_provider.py` (usage: input/output_tokens → unified)
- `app/providers/openai_provider.py` (usage: input/output_tokens + legacy keys → unified)
- `app/providers/gemini_provider.py` (usage: usageMetadata camelCase → unified)
- `tests/test_providers.py` (7 novos testes)

---

### #2 - Adicionar alertas de limite diário de tokens ao health_summary ✅

**Prioridade**: 🔴 Alta  
**Status**: ✅ Completed (2026-05-20)  
**Deps**: #1 (telemetria)

Integrar sinais de alerta diários para consumo de tokens. Avisos quando o
total agregado de tokens do dia ultrapassa o limite configurável.

**Critérios de conclusão**:
- [x] Sinal `daily_tokens_high` adicionado ao `health_summary.signals`
- [x] Threshold configurável via `AI_DAILY_TOKEN_ALERT_THRESHOLD` (env var)
- [x] `daily_token_total` e `daily_token_threshold` expostos no summary
- [x] `--health-only` inclui `daily_token_total`/`daily_token_threshold` em `checks`
- [x] Comportamento desabilitado por default (`threshold = 0`) preserva compatibilidade
- [x] Testes cobrindo cenários acima do limite, desabilitado e health-only (3 novos)

**Arquivos afetados**:
- `app/commands/diagnose_orchestrator.py` (sinal e checks)
- `docs/references.md` (env var documentada)
- `tests/test_command_entrypoints.py` (3 novos testes)

**Escopo**:
- Alerta baseado apenas em **limite diário de tokens** (não USD). O total
  de tokens em `daily_token_total` é o sinal canônico de consumo.

---

### #3 - Refinar limites de token por tarefa/perfil/modelo

**Prioridade**: 🟡 Média  
**Status**: ⏳ Pending  
**Deps**: #1

Implementar granularidade em 3 níveis: por tarefa, por perfil do projeto, por modelo.

**Critérios de conclusão**:
- [ ] `provider_max_tokens` suporta 3 níveis de granularidade
- [ ] Documentado em `docs/references.md`
- [ ] Testes cobrindo override hierarchy
- [ ] Backwards compatible com config existente

**Arquivos afetados**:
- `app/core/routing/router.py` (lógica de override)
- `app/models/config_models.py` (schema)
- `docs/references.md` (documentação)
- `tests/unit/routing/` (testes)

---

## 🔒 Fase 2: Segurança & Cobertura (2-3 semanas)

### #4 - Hardening de segurança de contexto

**Prioridade**: 🔴 Alta  
**Status**: ⏳ Pending  
**Deps**: Nenhuma

Guardrails contra vazamento de secrets e prompt injection de conteúdo de repositório.

**Critérios de conclusão**:
- [ ] Detector de secrets integrado ao `ContextManager`
- [ ] Filtros de prompt injection para conteúdo dinâmico
- [ ] Logs de bloqueios/sanitização para auditoria
- [ ] Testes cobrindo padrões comuns (API keys, tokens, SQL)
- [ ] Documentação de guardrails em `docs/`

**Arquivos afetados**:
- `app/core/context/context_manager.py` (sanitização)
- `app/core/security/` (novo módulo)
- `tests/security/` (novo)
- `docs/security.md` (novo)

---

### #5 - Expandir seleção de arquivos além de Python

**Prioridade**: 🟡 Média  
**Status**: ⏳ Pending  
**Deps**: Nenhuma

Suporte para TypeScript, Go, Java, C++. Ranking heuristics genéricas.

**Critérios de conclusão**:
- [ ] Detector de linguagem de projeto
- [ ] Ranking heuristics para 4+ linguagens
- [ ] `task_file_limits` e `task_queries` multi-linguagem
- [ ] Testes cobrindo rankings por linguagem
- [ ] Documentação em `docs/operations.md`

**Arquivos afetados**:
- `app/core/ranking/` (novo)
- `app/core/context/file_selector.py` (refactor)
- `tests/unit/ranking/` (novo)
- `docs/operations.md` (atualizar)

---

## ⚡ Fase 3: Recursos Avançados (2-3 semanas)

### #6 - Implementar execução com streaming para tarefas longas

**Prioridade**: 🟡 Média  
**Status**: ⏳ Pending  
**Deps**: Nenhuma

Streaming de resposta para providers que suportam. Pipeline mantém progresso e permite interrupção graceful.

**Critérios de conclusão**:
- [ ] Interface de streaming no provider abstrato
- [ ] Implementação para 2+ providers (Claude + OpenAI)
- [ ] Pipeline `TaskRunner` com streaming
- [ ] Testes E2E com timeout e interrupção
- [ ] Documentação do comportamento

**Arquivos afetados**:
- `app/core/providers/base.py` (interface streaming)
- `app/core/providers/claude/` (implementação)
- `app/core/providers/openai/` (implementação)
- `app/core/task_runner.py` (integração)
- `tests/integration/streaming/` (novo)

---

### #7 - Definir formato de output produtizado para auditorias

**Prioridade**: 🟡 Média  
**Status**: ⏳ Pending  
**Deps**: Nenhuma

Schema JSON padrão para auditorias de código e revisões. Relatório estruturado com achados, severidade, recomendações.

**Critérios de conclusão**:
- [ ] Schema JSON para código/revisão output
- [ ] Template de relatório estruturado
- [ ] Exemplos para 2-3 tipos de tarefa
- [ ] Integração com task result cache
- [ ] Documentação do formato em `docs/`

**Arquivos afetados**:
- `app/models/output_models.py` (novo)
- `app/core/output/formatter.py` (novo)
- `docs/output-format.md` (novo)
- `examples/output/` (novo)

---

## 🔗 Fase 4: Integrações (1-2 semanas)

### #8 - Avaliar integração com GitHub PR para workflows de revisão

**Prioridade**: 🟢 Baixa  
**Status**: ⏳ Pending  
**Deps**: #7 (formato de output)

Prototipo de integração GitHub API. Comentários em PRs, sugestões de mudanças, labels automáticas.

**Critérios de conclusão**:
- [ ] Prototipo funcional lendo PR e arquivos
- [ ] Suporte para comentários na PR
- [ ] Suporte para suggested changes
- [ ] Configuração via `project.yaml`
- [ ] Documentação do workflow
- [ ] Decision document: fazer vs não fazer

**Arquivos afetados**:
- `app/integrations/github/` (novo)
- `app/models/config_models.py` (atualizar)
- `docs/github-pr-integration.md` (novo)
- `tests/integration/github/` (novo)

---

## 📊 Timeline

| Fase | Duração | Início | Fim |
|------|---------|--------|-----|
| 1 | 2-3 sem | 2026-05-20 | 2026-06-10 |
| 2 | 2-3 sem | 2026-06-10 | 2026-07-01 |
| 3 | 2-3 sem | 2026-07-01 | 2026-07-22 |
| 4 | 1-2 sem | 2026-07-22 | 2026-08-05 |

**Total estimado**: 7-11 semanas

---

## 🔄 Rastreamento

Use o sistema de tarefas para rastrear progresso:

```bash
# Ver todas as tarefas
TaskList

# Iniciar uma tarefa
TaskUpdate --taskId 1 --status in_progress

# Completar uma tarefa
TaskUpdate --taskId 1 --status completed
```

---

## 📝 Notas

- Cada tarefa tem critérios de conclusão explícitos
- Dependências são rastreadas para sequenciar o trabalho
- Testes são inclusos em cada etapa
- Documentação é entregue junto com código
- Timeline pode ser ajustada baseado em descobertas durante implementação

---

## 🚀 Próximo Passo

Iniciar **Tarefa #1** (Normalizar telemetria de uso).

Ver: `TaskUpdate --taskId 1 --status in_progress`
