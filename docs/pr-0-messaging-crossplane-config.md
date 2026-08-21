# PR-0 — Crossplane config por Environment

**Branch:** `feat/messaging-pr-0-crossplane-config`  
**Jira:** NS-190  
**ADR:** [002-messaging-org-level-catalog.md](../adrs/002-messaging-org-level-catalog.md)

## Summary

- Configuração Crossplane **por environment** como recurso dedicado (`environment_crossplane_configs`), não no bag genérico de settings.
- Bounded context `api/app/crossplane/` (api / core / infra): config, validação e probe de health.
- UI em Environments para habilitar Crossplane, escolher o cluster e informar região / conta AWS / provider config.
- Validação no save: campos obrigatórios quando `enabled=true`, cluster do mesmo environment, e probe live de Crossplane healthy no cluster.
- Coluna **Crossplane** na listagem de Clusters (mesmo padrão do Gateway API): status live via probe do BC Crossplane — **sem** flag manual `crossplane_available`.
- Prepara sync de messaging (PRs seguintes): Topic/Queue **não** carregam `region` / `provider_config` no payload — herdam do environment.

## Bounded context

| Responsabilidade | Onde |
|------------------|------|
| Config por env + save/validate | `crossplane/` (service, validators, repo, handlers) |
| Probe live (`available` / `healthy` / `providers`) | `crossplane/infra/k8s_crossplane_probe.py` → `K8sClient.check_crossplane_status` |
| Listagem de Clusters embute status | `ClusterService` recebe `probe_crossplane` **injetado** no composition root (`cluster_handlers`); core de Clusters **não** chama Crossplane APIs direto |
| DTO de status (`CrossplaneFeatures`) | `crossplane/api/crossplane_dto.py` (Clusters só compõe no response) |

`ClusterUpdate` / update de gateway **não** mudam nesta PR — permanecem iguais a `main` (`ClusterCreate` no PUT).

## Justificativa das configs (envs / campos)

Crossplane é **por environment**, não por Topic/Queue: um env tem um cluster K8s fixo para sync de messaging e uma conta/região AWS. Isso evita drift e ARNs pré-montados no Jinja.

Mapeamento legado (settings bag) → recurso atual:

| Setting legado | Campo atual | Por que é necessário | Onde é utilizado |
|----------------|-------------|----------------------|------------------|
| `crossplane_enabled` | `enabled` | Gate: sem isso o Tron **não** aplica Managed Resources SNS/SQS. Environments sem messaging Crossplane ficam desligados. | Save da config; `resolve_context_for_sync` — se `false`, sync de messaging não provisiona |
| `crossplane_cluster_uuid` | `cluster_uuid` | Messaging usa **cluster fixo** do env (não o cluster do workload / least-load). Evita Managed Resources órfãos se o cluster de deploy mudar. | Resolve `K8sClient` no sync; no save, probe de health do Crossplane nesse cluster |
| `crossplane_aws_region` | `aws_region` | Região dos recursos AWS. **Input explícito** — `ClusterProviderConfig` / provider AWS **não** guardam region; cada MR precisa de `spec.forProvider.region`. | Templates Jinja (`region:` em Topic/Queue/Subscription); validação no save |
| `crossplane_provider_config` | `provider_config` | Nome do `ClusterProviderConfig` no cluster (ex.: `default`). Define credenciais/endpoint AWS (IRSA em stg, Secret+Floci no local). | Templates: `providerConfigRef.name` + `kind: ClusterProviderConfig` |

### `aws_account_id` (também no recurso)

Não existia na lista antiga de keys do settings bag, mas faz parte da config atual:

| Campo | Por que é necessário | Onde é utilizado |
|-------|----------------------|------------------|
| `aws_account_id` | Montar ARNs/URLs de display e contexto de IAM nos templates. A account **não** vem do `ClusterProviderConfig` quando `skip_requesting_account_id` está ativo (ex.: Floci local). | Enrichment / sync messaging; validação de 12 dígitos no save |

### Resumo

- **enabled** → liga/desliga provisionamento Crossplane no env  
- **cluster_uuid** → *onde* aplicar os manifests (cluster Crossplane do env)  
- **aws_region** → *em qual região AWS* criar SNS/SQS  
- **provider_config** → *com quais credenciais* o provider AWS fala com a conta  
- **aws_account_id** → *qual conta* para ARNs/contexto (sem inferir do provider)

### Regras de validação no save

Com `enabled=true`:

1. Todos os campos acima são obrigatórios.
2. O cluster deve pertencer ao mesmo environment.
3. Crossplane deve estar **installed + healthy** no cluster (probe live via `probe_crossplane_health` / BC Crossplane).

Com `enabled=false`, a config pode ser salva sem os demais campos (e sem probe).

O probe de health no **save da env** roda só nesse caminho — não a cada resolve de sync — para que outages temporários do control plane não bloqueiem leituras do catálogo.

A coluna na listagem de Clusters usa o **mesmo** probe (informativo Available / Unhealthy / Not Available + providers).

### UI — modal Environments

Save fica desabilitado até o GET da config Crossplane completar (evita gravar draft vazio e apagar config existente).

## Commits

| Commit | Descrição |
|--------|-----------|
| `e9703d9` | feat(environments): add Crossplane cluster and environment config |
| `253d494` | feat(clusters): allow Crossplane-only edits without resubmitting token |
| `59705d3` | feat(crossplane): store config as a dedicated environment resource |
| `630669e` | feat(crossplane): add aws_account_id to environment Crossplane config |
| `682f8cf` | fix(environments): show Crossplane errors inside the modal |
| `811a27d` | docs(adr): expand messaging org-level catalog ADR |

## Test plan

- [ ] Abrir Environments → Crossplane: listar todos os clusters do env
- [ ] Abrir modal: Save desabilitado / “Loading…” até o GET; depois form editável
- [ ] Salvar com `enabled=false` sem demais campos → sucesso
- [ ] Salvar com `enabled=true` sem region/account/provider/cluster → erro de validação
- [ ] Salvar com cluster de outro environment → erro
- [ ] Salvar com Crossplane unhealthy/ausente no cluster → erro no modal
- [ ] Salvar com Crossplane healthy + campos válidos → config persistida e retornada no GET
- [ ] Clusters list: coluna Crossplane reflete Available / Unhealthy / Not Available (live)
- [ ] Update de cluster (gateway/token) continua funcionando sem regressão (igual `main`)

## Screenshots

### Environments — modal Crossplane

<!-- print: modal aberto com config carregada -->

<!-- print: Save desabilitado / loading enquanto GET -->

<!-- print: erro de validação / Crossplane unhealthy no modal -->

### Clusters — coluna Crossplane

<!-- print: listagem com Available / Unhealthy / Not Available -->
