# RFC-001 — Provedor de nuvem AWS

**Status:** Adotada na infraestrutura versionada.

## Contexto

O projeto exige executar a API da Oficina, expor acesso HTTP, manter dados relacionais e observar o cluster. Este repositório Terraform usa AWS em `us-east-1` e uma role IAM preexistente (`LabRole`); o banco e a aplicação estão em repositórios separados.

## Problema

Escolher uma plataforma que reúna rede, execução Kubernetes, entrada de APIs, banco gerenciado e integração com Lambda sem operar esses serviços dentro da aplicação.

## Alternativas consideradas

- Hospedar aplicação e PostgreSQL em máquinas virtuais autogeridas: mais controle, porém mais trabalho de operação e escalabilidade.
- Executar Kubernetes e banco em outro provedor: exigiria substituir integrações AWS já presentes; não há avaliação comparativa de custos ou desempenho no código.
- Usar somente containers sem EKS: reduziria a camada Kubernetes, mas não corresponderia aos manifests e providers implementados.

## Proposta adotada

AWS com VPC, duas subnets públicas e duas privadas, Internet Gateway, NAT Gateways, EKS/node group/add-ons, ECR, AWS Load Balancer Controller, NLB TCP/80, API Gateway HTTP API com VPC Link, Lambdas de CPF referenciada e authorizer JWT criada, Secrets Manager e CloudWatch Logs. `database-infra` configura RDS PostgreSQL privado. O Terraform usa backend S3 com `use_lockfile = true` para state; a implantação da aplicação lê outputs dos states externos. New Relic é serviço externo integrado via Helm.

## Justificativa

Os recursos permitem ligar o Gateway ao cluster pela VPC, separar o banco em subnets privadas, manter imagens em ECR e aplicar observabilidade Kubernetes. A decisão reflete a infraestrutura existente, não uma comparação medida entre provedores.

## Consequências positivas

Rede e serviços gerenciados compartilham a mesma VPC; Helm instala integrações no EKS; outputs permitem que outros repositórios consumam identificadores sem recriar a rede.

## Trade-offs

Há acoplamento a serviços AWS e dependência de IAM/credenciais existentes. A Lambda CPF é externa, e este repositório não controla seu código. O RDS atual é Single-AZ. Rotas Gateway, alvos do target group e Deployment são responsabilidades separadas e dependem de configuração compatível. O Gateway authorizer também exige conferir formato de evento e ARN do segredo.

**Evidências:** `terraform/{main,vpc,eks,ecr,networking,api_gateway,lambda_authorizer,secrets,monitoring,outputs}.tf`, `../database-infra/terraform/main.tf`.
