# ADR-002 — Amazon EKS para executar a aplicação

**Status:** Adotada na infraestrutura e nos manifests da aplicação.

## Contexto

A aplicação é empacotada em container e seu repositório possui Deployment, Service, probes, HPA e TargetGroupBinding Kubernetes.

## Decisão

Provisionar EKS com node group gerenciado em subnets privadas, add-ons VPC CNI/CoreDNS/kube-proxy e AWS Load Balancer Controller via Helm. A aplicação é implantada em namespace `oficina` por outro repositório.

## Justificativa

Kubernetes oferece Deployment/Service, health probes e HPA coerentes com os manifests; o plano de controle gerenciado evita mantê-lo em VMs próprias.

## Consequências

O cluster e a aplicação podem evoluir em repositórios separados. Há custo e operação de nodes, controllers e métricas; a role IAM existente é reutilizada. O controller instalado usa credenciais temporárias conforme scripts/pipeline, que precisam ser renovadas quando a sessão expira. O EKS por si não comprova pods saudáveis ou rota de entrada funcional.

## Alternativas consideradas

- EC2 com aplicação direta: reduziria Kubernetes, mas não executaria os manifests existentes.
- Cluster Kubernetes autogerido: exigiria operação do plano de controle e upgrades próprios.

**Evidências:** `terraform/eks.tf`, `scripts/sync-lb-controller-credentials.sh`, `../tech-challenge-fiap/k8s/`.
