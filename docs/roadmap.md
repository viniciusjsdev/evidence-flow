# Evidence Flow Roadmap

Este documento registra o estado atual do `evidence-flow` e o que ainda falta
para transformar o scaffold inicial em um harness operacional completo.

## Estado atual

O projeto ja possui a fundacao de Harness:

- estrutura de diretorios do repositorio;
- `README.md` e `AGENTS.md`;
- contratos JSON Schema para:
  - `domain_context`;
  - `tracks`;
  - `search_plan`;
  - `discovery_sessions`;
  - `source_inventory`;
  - `handoff`;
  - `manifest`;
- exemplos validaveis em `contexts/examples/`;
- core Python minimo:
  - `ArtifactStore`;
  - `RunState`;
  - `ContractValidator`;
  - `HarnessOrchestrator`;
- perfis operacionais separados:
  - `TrackPlannerProfile`;
  - `FixtureDiscoveryProfile`;
  - `ZeroResultDiscoveryProfile`;
  - `FilterValidateProfile`;
  - `SemanticEnrichmentProfile`;
  - `RankAccessProfile`;
  - `HandoffBuilderProfile`;
- CLI minima com:
  - `validate-context`;
  - `validate-tracks`;
  - `validate-handoff`;
  - `validate-manifest`;
  - `init-run`;
  - `discovery-to-handoff`;
- testes cobrindo contratos e fluxo inicial.

Hoje o harness ja consegue transformar:

```text
contexto + trilhas
  -> plano de busca
  -> sessoes brutas de discovery por fixture ou zero-result
  -> fontes filtradas
  -> fontes enriquecidas heuristicamente
  -> inventario rankeado
  -> handoff de coleta
```

O ponto importante: o fluxo ja preserva artefatos por etapa e valida contratos,
mas ainda nao executa busca externa real nem coleta operacional real.

## O que falta

### 1. Search adapters reais

Objetivo:

Substituir o `FixtureDiscoveryProfile` por adapters que executem descoberta real
sem alterar os contratos downstream.

Adapters candidatos:

- `PerplexitySearchAdapter`, inspirado no `Research_FREnTE`;
- `WebSearchAdapter`;
- `ScholarlySearchAdapter`;
- adapters especificos por catalogo ou dominio.

Entregas esperadas:

- interface `SearchAdapter`;
- implementacao inicial API-first;
- persistencia de request/response bruto;
- tratamento de `ok`, `zero_result`, `blocked` e `error`;
- testes com fixture e mocks.

### 2. LLM adapter e enriquecimento controlado

Objetivo:

Permitir enriquecimento semantico por LLM sem deixar a LLM fundar a verdade do
dominio.

Entregas esperadas:

- interface `LLMAdapter`;
- prompt contract para extracao de metadados;
- `SemanticEnrichmentProfile` com modo `heuristic`, `llm` e `hybrid`;
- campos de metodo, modelo, confianca ou status de revisao;
- regra explicita: a LLM nao altera `domain_layer`, `hierarchy_level` nem
  `thematic_axis`, que devem vir das trilhas.

### 3. Access ranking mais robusto

Objetivo:

Melhorar a classificacao de acesso e priorizacao sem introduzir scores opacos.

Entregas esperadas:

- regras por extensao, dominio, formato e hint de coleta;
- classificacao de acesso:
  - `direct_download`;
  - `api_access`;
  - `web_portal`;
  - `geospatial_platform`;
  - `pdf_extraction`;
  - `restricted`;
  - `manual`;
  - `unknown`;
- explicacao textual do motivo do ranking;
- matriz de cobertura por trilha, camada e formato.

### 4. Handoff operacional completo

Objetivo:

Transformar o handoff em contrato suficiente para um coletor agir sem conversa
adicional.

Entregas esperadas:

- `handoff.json` com targets completos;
- `harvester_targets.csv`;
- matriz de cobertura temporal;
- lacunas por fonte, camada, variavel e periodo;
- politica de completude do handoff;
- validacao que bloqueia targets sem URL, acesso, formato ou status.

### 5. Collection adapters

Objetivo:

Executar a coleta operacional mantendo bruto antes de interpretacao.

Adapters candidatos:

- `HttpDownloadCollector`;
- `ApiCollector`;
- `PortalManualCollector`;
- `BrowserDiscoveryCollector`;
- `PdfExtractionCollector`;
- `GeospatialExportCollector`.

Entregas esperadas:

- interface `CollectionAdapter`;
- manifest por target;
- status por target:
  - `collected`;
  - `partial`;
  - `blocked`;
  - `error`;
  - `not_attempted`;
- checksums, media type, tamanho e URL de origem;
- registro de login, captcha, email, aprovacao manual ou outro bloqueio.

### 6. Raw artifact store mais forte

Objetivo:

Garantir rastreabilidade completa entre fonte externa, bruto, staging e analytic.

Entregas esperadas:

- contrato de artefato bruto;
- checksum SHA-256;
- manifest de arquivos coletados;
- relacao entre target e arquivos;
- notas de perda de cobertura ou coleta parcial.

### 7. Staging contracts

Objetivo:

Formalizar a passagem de bruto para dados harmonizados.

Entregas esperadas:

- `staging.schema.json`;
- dataset manifest com:
  - path;
  - fonte;
  - schema;
  - chave temporal;
  - chave espacial;
  - unidade;
  - granularidade;
  - periodo real;
  - periodo alvo;
  - lacunas;
  - regras de limpeza;
  - relacao com artefatos brutos;
- validadores de colunas e tipos.

### 8. Analytic contracts

Objetivo:

Formalizar datasets derivados prontos para analise.

Entregas esperadas:

- `analytic.schema.json`;
- registro de transformacoes;
- chaves de juncao;
- cobertura por variavel;
- agregacoes e derivacoes documentadas;
- matriz de cobertura comparando alvo e real.

### 9. EDA generator

Objetivo:

Gerar EDA orientada pela pergunta, nao graficos genericos.

Entregas esperadas:

- contrato de figura;
- cada figura declara:
  - pergunta respondida;
  - dados usados;
  - cobertura real;
  - juncao usada;
  - limites interpretativos;
- perfil `EDAGeneratorProfile`;
- output em `runs/{run-id}/eda/figures/`.

### 10. Report context builder

Objetivo:

Separar calculo analitico de narrativa final.

Entregas esperadas:

- `report_context.schema.json`;
- `report_context.json` consumindo:
  - figuras finais;
  - metricas calculadas;
  - fontes;
  - lacunas;
  - notas metodologicas;
  - cobertura;
  - blockers;
- perfil `ReportContextBuilderProfile`.

### 11. Renderer adapters

Objetivo:

Permitir que o mesmo contexto estruturado gere diferentes saidas.

Adapters candidatos:

- Markdown;
- HTML;
- dashboard;
- slide deck.

Entregas esperadas:

- interface `RendererAdapter`;
- renderer Markdown inicial;
- renderer HTML depois, inspirado no padrao visual de `Research_FREnTE`;
- nenhuma recomputacao silenciosa dentro do renderer.

### 12. Learning e memoria

Objetivo:

Registrar aprendizados sem misturar run artifacts, memoria duravel e heuristicas
de agente.

Entregas esperadas:

- contrato de learning note;
- destino para aprendizado local do run;
- destino para memoria procedural;
- regras de promocao para skills;
- diagnosticos de falhas recorrentes.

### 13. Perfis e role contracts

Objetivo:

Trazer a disciplina de perfis do `research-harness` para as operacoes do
`evidence-flow`.

Perfis esperados:

- `ResearchLeadProfile`;
- `TrackPlannerProfile`;
- `DiscoveryProfile`;
- `FilterValidateProfile`;
- `SemanticEnrichmentProfile`;
- `AccessRankerProfile`;
- `HandoffBuilderProfile`;
- `HarvesterProfile`;
- `StagingBuilderProfile`;
- `AnalyticBuilderProfile`;
- `EDAGeneratorProfile`;
- `ReportContextProfile`;
- `RendererProfile`;
- `EvidenceAuditorProfile`;
- `LearningProfile`.

Cada perfil deve ter:

- objetivo;
- input minimo;
- output minimo;
- contrato validavel;
- failure modes;
- politica de promocao;
- proximo perfil esperado.

### 14. CLI por etapas

Objetivo:

Permitir executar e repetir etapas sem rodar tudo sempre.

Comandos desejados:

- `plan-tracks`;
- `discover`;
- `filter-sources`;
- `enrich-sources`;
- `rank-access`;
- `build-handoff`;
- `collect`;
- `build-staging`;
- `build-analytic`;
- `build-report-context`;
- `render`;
- `audit-run`;
- `resume-run`.

### 15. Auditoria de run

Objetivo:

Dar ao harness a capacidade de dizer se uma execucao esta pronta para avancar.

Entregas esperadas:

- checklist por etapa;
- validacao de artefatos obrigatorios;
- contagem de lacunas e blockers;
- status final:
  - `ready`;
  - `partial`;
  - `blocked`;
  - `error`;
- relatorio Markdown de auditoria.

## Ordem recomendada

### Fase 1 - Discovery real

1. Criar `SearchAdapter`.
2. Implementar adapter inicial API-first.
3. Manter fixture e zero-result como modos de teste.
4. Garantir que `discovery_sessions` continue sendo o contrato comum.

### Fase 2 - Handoff forte

1. Expandir `handoff.schema.json`.
2. Gerar CSV de targets.
3. Adicionar cobertura por camada/trilha/periodo.
4. Criar auditoria de handoff.

### Fase 3 - Coleta operacional

1. Criar `CollectionAdapter`.
2. Implementar HTTP download e API collector.
3. Registrar artefatos brutos e blockers.
4. Validar collection manifest.

### Fase 4 - Dados tratados

1. Criar contratos de staging.
2. Criar contratos analytic.
3. Criar coverage matrix.
4. Criar registry de join keys.

### Fase 5 - EDA e relatorio

1. Criar contrato de figura.
2. Criar `report_context.schema.json`.
3. Implementar renderer Markdown.
4. Implementar renderer HTML.

### Fase 6 - Aprendizado

1. Criar learning notes.
2. Definir promocao para skills.
3. Implementar audit-run.
4. Criar memoria procedural do harness.

## Regra de direcao

O `evidence-flow` deve continuar generico, mas nao abstrato demais.

Toda nova funcionalidade deve preservar:

- contexto explicito;
- trilhas declaradas;
- bruto antes de interpretacao;
- contratos validaveis;
- handoff como artefato;
- lacunas visiveis;
- separacao entre fonte, dado, analise e narrativa;
- perfis com responsabilidades pequenas e testaveis.

