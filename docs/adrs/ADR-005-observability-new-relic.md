# ADR-005 — New Relic para observabilidade

**Status:** Integração configurada; painéis e alertas específicos não comprovados.

## Contexto

O Tech Challenge requer visibilidade de latência, recursos Kubernetes, saúde, falhas, logs correlacionados, volume de ordens, tempo por status e integrações. Este repositório já grava access logs do Gateway no CloudWatch e instala `nri-bundle` no EKS.

## Decisão

Instalar New Relic via Helm no namespace `newrelic`, com kube-state-metrics, eventos Kubernetes e encaminhamento de logs de containers. O código da aplicação configura logs JSON com `correlation_id`, duração/status HTTP, agente APM condicionado à chave e eventos `ServiceOrderCreated` e `IntegrationError`.

## Justificativa

O bundle observa nodes/pods e coleta logs; o agente e os eventos da aplicação dão contexto de requisições e integração. São os mecanismos efetivamente encontrados.

## Consequências

CPU/memória e eventos do cluster, logs JSON da aplicação e erros CPF podem chegar ao New Relic quando o chart e o agente estão ativos. Access logs com latência permanecem no CloudWatch; não há encaminhamento CloudWatch → New Relic configurado aqui. Probes e health check `/health` existem, mas monitor sintético/alerta de uptime não foi encontrado. Volume diário pode ser calculado dos eventos de criação recebidos; tempo médio por status e alerta específico para falhas de ordens não estão implementados. A chave New Relic é sensível e fornecida pela pipeline/Secret.

## Alternativas consideradas

- Somente CloudWatch: já cobre access logs do Gateway, mas não a integração Kubernetes/APM encontrada.
- Prometheus autogerido: exigiria operação e configuração não presentes neste repositório.

**Evidências:** `terraform/{monitoring,api_gateway}.tf`, `../tech-challenge-fiap/src/{api/main.py,infrastructure/observability/}`, `../tech-challenge-fiap/src/application/usecases/ordem_servico/abrir_os.py`.
