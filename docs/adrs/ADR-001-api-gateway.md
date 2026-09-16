# ADR-001 — API Gateway como entrada das APIs

**Status:** Adotada para a infraestrutura compartilhada.

## Contexto

O cliente precisa de um endpoint HTTP para a Oficina e de uma integração com a Lambda CPF existente. O Terraform define HTTP API, stage `$default`, CORS, access logs e integrações; as rotas foram removidas deste repositório.

## Decisão

Usar API Gateway HTTP API como entrada. A integração `HTTP_PROXY` alcança o listener NLB por VPC Link; a integração `AWS_PROXY` invoca a Lambda CPF se uma rota for associada. O authorizer `REQUEST` pode ser associado às rotas protegidas onde elas forem criadas.

## Justificativa

Concentra endpoint, integrações, controle de entrada e access logs JSON sem expor diretamente os pods da aplicação ao Gateway.

## Consequências

O Gateway registra `requestId`, status e latência no CloudWatch. Disponibilidade de endpoints depende de rotas e alvos fora deste Terraform. O NLB é público na configuração atual, e o target group exige verificação de compatibilidade com o binding `ip` da aplicação.

## Alternativas consideradas

- Cliente acessando diretamente o NLB: dispensaria Gateway e VPC Link, mas perderia os recursos de entrada aqui configurados.
- Ingress Kubernetes como entrada única: exigiria outro caminho de exposição não implementado neste repositório.

**Evidências:** `terraform/{api_gateway,networking}.tf`, `docs/api-gateway-routes.md`.
