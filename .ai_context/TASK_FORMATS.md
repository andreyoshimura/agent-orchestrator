# agent-orchestrator - Task Formats

Define formatos padrao para respostas de IA neste repositorio, com foco em clareza, baixo consumo de tokens e seguranca operacional.

## Formato padrao

### Diagnostico

- Maximo 5 linhas.
- Explicar o ponto central sem recontar o projeto inteiro.

### Evidencia

- Maximo 5 bullets.
- Citar arquivos, comandos ou outputs relevantes.

### Acao recomendada

- Maximo 5 bullets.
- Deve ser executavel e segura.

### Risco

- Maximo 3 bullets.
- Explicar impacto em runtime, providers, routing, budget ou storage quando aplicavel.

### Proximo passo

- Uma unica acao concreta.

## Formato para alteracao de codigo

Responder com:

1. Escopo declarado.
2. Arquivos afetados.
3. Motivo da alteracao.
4. Risco operacional.
5. Como validar.

## Formato para diagnostico operacional

Responder com:

1. Comando executado.
2. Status observado.
3. Evidencia.
4. Hipotese.
5. Proximo passo seguro.

## Regras de economia de contexto

- Nao repetir README inteiro.
- Nao listar estrutura completa sem necessidade.
- Nao colar logs longos.
- Nao abrir `var/cache` ou `var/state` por padrao.
- Nao explicar conceitos ja documentados, apenas apontar para o arquivo relevante.

## Quando pedir mais contexto

Pedir somente o arquivo ou comando minimo necessario.

Evitar pedidos amplos como:

- "mande o repo todo"
- "liste todos os arquivos"
- "cole todos os logs"

## Respostas longas

Somente responder longo se o usuario pedir explicitamente:

- detalhado
- completo
- profundo
- auditoria completa

Caso contrario, manter resposta compacta.
