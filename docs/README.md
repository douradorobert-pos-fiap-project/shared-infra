# Documentação da arquitetura

Esta documentação descreve a solução Oficina do Tech Challenge FIAP conforme os arquivos versionados. A infraestrutura compartilhada deste repositório define VPC, EKS, NLB, API Gateway HTTP API, integrações Lambda, authorizer JWT, ECR, CloudWatch e New Relic. O RDS/PostgreSQL está no repositório local `database-infra`; API, migrations, rotas e objetos Kubernetes da Oficina estão em `tech-challenge-fiap`. Os diagramas representam a ligação entre esses recursos quando as configurações dos três repositórios são aplicadas de forma compatível. Eles não comprovam que o ambiente AWS esteja ativo.

Comece pelo [diagrama de componentes](architecture/component-diagram.md), siga os [fluxos de autenticação e ordem de serviço](architecture/sequence-diagrams.md) e consulte o [modelo de dados](architecture/database-design.md). As [rotas antes removidas deste repositório](api-gateway-routes.md) são referência histórica, não prova de rotas atualmente criadas aqui.

## Arquitetura e diagramas

| Documento | Fonte Mermaid |
| --- | --- |
| [Componentes](architecture/component-diagram.md) | [components.mmd](diagrams/components.mmd) |
| [Sequências](architecture/sequence-diagrams.md) | [authentication-sequence.mmd](diagrams/authentication-sequence.mmd) e [service-order-sequence.mmd](diagrams/service-order-sequence.mmd) |
| [Banco de dados](architecture/database-design.md) | [database-er.mmd](diagrams/database-er.mmd) |

## RFCs

- [RFC-001 — Provedor de nuvem](rfcs/RFC-001-cloud-provider.md)
- [RFC-002 — Banco de dados](rfcs/RFC-002-database.md)
- [RFC-003 — Autenticação](rfcs/RFC-003-authentication.md)

## ADRs

- [ADR-001 — API Gateway](adrs/ADR-001-api-gateway.md)
- [ADR-002 — Amazon EKS](adrs/ADR-002-kubernetes-eks.md)
- [ADR-003 — HPA](adrs/ADR-003-hpa.md)
- [ADR-004 — PostgreSQL/RDS](adrs/ADR-004-database-postgresql.md)
- [ADR-005 — New Relic](adrs/ADR-005-observability-new-relic.md)

## Alcance da evidência

O Terraform daqui não contém `aws_apigatewayv2_route`, RDS, Deployment, Service ou HPA da aplicação. O documento de rotas existente descreve rotas removidas; o endpoint da FastAPI para abrir ordem é `POST /api/v1/ordens-servico`, mas seu vínculo atual no Gateway não é demonstrado aqui. O target group Terraform não declara `target_type`, enquanto o `TargetGroupBinding` da aplicação declara `ip`; a compatibilidade e o registro real dos pods exigem verificação do ambiente. A Lambda CPF externa é referenciada, sem seu código neste repositório. A abertura de ordem não a chama no código da aplicação; ela é invocada no cadastro de cliente quando configurada. O RDS não está em Multi-AZ (`multi_az = false`).

As fontes externas locais utilizadas na análise são `../database-infra/terraform/main.tf`, `../tech-challenge-fiap/migrations/versions/001_initial_schema.py`, `../tech-challenge-fiap/src/infrastructure/database/models/`, `../tech-challenge-fiap/src/application/usecases/ordem_servico/abrir_os.py` e `../tech-challenge-fiap/k8s/`. Estes caminhos são referências de auditoria, não dependências da documentação publicada neste repositório.

As alternativas em RFCs e ADRs são comparações técnicas feitas para esta documentação. O código não registra avaliações históricas, provas de conceito ou benchmarks dessas alternativas.
