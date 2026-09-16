# ADR-003 — Escalabilidade horizontal com HPA

**Status:** Manifestado no repositório da aplicação; não provisionado neste Terraform.

## Contexto

O Deployment `oficina-api` define requests e limits de CPU/memória e começa com duas réplicas. O repositório da aplicação contém `metrics-server.yaml` e `hpa.yaml`.

## Decisão

Usar HPA `autoscaling/v2` para escalar o Deployment entre 2 e 10 pods, com metas de CPU 70% e memória 80%. O manifest configura estabilização de subida de 30 s e de descida de 300 s.

## Justificativa

CPU/memória são métricas de recurso disponíveis ao Kubernetes e correspondem aos requests definidos no Deployment. Isso permite ajustar réplicas em vez de manter uma contagem fixa.

## Consequências

O HPA depende do metrics-server e da capacidade do node group; o node group Terraform tem mínimo 1, desejado 2 e máximo 4 nodes por padrão. O ajuste de pods não garante automaticamente capacidade de nodes ou métricas de negócio. Não há medição de carga ou teste de escala comprovado nestes arquivos.

## Alternativas consideradas

- Réplicas fixas: operação mais simples, mas sem resposta automática às métricas.
- Escala por métricas de ordens/latência: exigiria adaptadores e métricas de escala não configurados.

**Evidências:** `terraform/eks.tf`, `../tech-challenge-fiap/k8s/{deployment,hpa,metrics-server}.yaml`.
