# Rotas do API Gateway - Documentação

> **Estado atual (2026-11):** a fonte de verdade das rotas é `terraform/api_gateway.tf`, em `local.application_routes`. Esta página contém abaixo material histórico de uma arquitetura anterior; não use a lista histórica para inferir as rotas atualmente publicadas.

Este arquivo documenta todas as rotas do API Gateway que foram implementadas no
Terraform de infraestrutura antes da separação de responsabilidades. As rotas
foram removidas do `iac-kubernetes` e devem ser recriadas no repositório da
aplicação.

> **Atualização de roteamento:** o desenho NLB descrito abaixo é histórico. A migração em andamento usa API Gateway → VPC Link → ALB interno gerenciado pelo AWS Load Balancer Controller. Os serviços compartilham o IngressGroup `sandbox-api`; o OS atende `/health`. A fase `finalize` do Terraform remove o NLB legado.

## Ordem para migrar o sandbox

1. Execute o workflow de infraestrutura com `phase=bootstrap`. Ele aplica as tags de descoberta às subnets privadas, cria o security group do ALB e instala o metrics-server. Copie o output `internal_alb_security_group_id`.
2. Defina `ALB_SECURITY_GROUP_ID` como variável do ambiente `sandbox` nos três repositórios de serviço.
3. Execute os workflows manuais dos serviços OS, Billing e Execution. Cada deploy aplica seu Ingress ao grupo interno `sandbox-api`.
4. Aguarde o ALB `sandbox-api-alb` e os respectivos target groups ficarem saudáveis.
5. Execute o workflow de infraestrutura com `phase=finalize`. Ele atualiza a integração do API Gateway para o listener HTTP do ALB e remove o NLB legado.
6. Verifique `GET /health` pelo endpoint do API Gateway e confirme que `metrics.k8s.io` está disponível para os HPAs.

O endpoint público pode ficar indisponível brevemente durante a troca da integração.

---

## Arquitetura Atual

```text
Clientes e notificações Mercado Pago
    │
    ▼
API Gateway HTTP API público (${var.environment}-api)
    │
    ├─ GET /health
    ├─ Rotas de negócio explícitas (autorização atual: NONE)
    └─ POST /api/v1/webhooks/mercado-pago (HMAC validado pelo Billing)
            │
            ▼
       VPC Link
            │
            ▼
       ALB interno (sandbox-api-alb)
            │
            ▼
       Ingresses dos microsserviços no EKS
```

Não há rota raiz `ANY /` nem rota curinga `ANY /{proxy+}`. A allowlist reduz os caminhos publicados, mas as rotas de negócio continuam sem autenticação de usuário nesta alteração. O endpoint de webhook valida `x-signature` no Billing; o ALB permanece interno.

## Recursos Compartilhados (permanecem no iac-kubernetes)

| Recurso | Nome | ID/ARN |
|---|---|---|
| API Gateway HTTP API | `${var.environment}-api` | `aws_apigatewayv2_api.http_api` |
| JWT Authorizer | `${var.environment}-jwt-authorizer` | `aws_apigatewayv2_authorizer.jwt` |
| VPC Link | `${var.environment}-vpclink` | `aws_apigatewayv2_vpc_link.main` |
| NLB | `${var.environment}-app-nlb` | `aws_lb.app_nlb` |
| NLB Target Group | `${var.environment}-app-tg` | `aws_lb_target_group.app` |
| NLB Listener | `${var.environment}-app-nlb` (porta 80) | `aws_lb_listener.app` |
| Lambda CPF Validator | `var.lambda_cpf_validator_name` | `data.aws_lambda_function.cpf_validator` |
| Lambda JWT Authorizer | `${var.environment}-jwt-authorizer` | `aws_lambda_function.authorizer` |

## Integrações Base (permanecem)

### Integração NLB (Aplicação via VPC Link)

- **Recurso:** `aws_apigatewayv2_integration.nlb_eks`
- **Tipo:** `HTTP_PROXY`
- **Connection Type:** `VPC_LINK`
- **Connection ID:** `aws_apigatewayv2_vpc_link.main.id`
- **Payload Format:** `1.0`
- **Method:** `ANY`
- **Timeout:** `30000ms`
- **Integration URI:** `aws_lb_listener.app.arn`

### Integração Lambda (CPF Validator)

- **Recurso:** `aws_apigatewayv2_integration.lambda_cpf`
- **Tipo:** `AWS_PROXY`
- **Connection Type:** `INTERNET`
- **Payload Format:** `2.0`
- **Timeout:** `30000ms`
- **Integration URI:** `data.aws_lambda_function.cpf_validator.invoke_arn`

## Rotas Removidas

### Rota 1: Health Check

- **Recurso:** `aws_apigatewayv2_route.health`
- **Route Key:** `GET /health`
- **Autorização:** `NONE`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`

### Rota 2: Login

- **Recurso:** `aws_apigatewayv2_route.auth_login`
- **Route Key:** `POST /api/v1/auth/login`
- **Autorização:** `NONE`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`

### Rota 3: CPF Validator

- **Recurso:** `aws_apigatewayv2_route.cpf`
- **Route Key:** `POST /cpf`
- **Autorização:** `NONE`
- **Integração:** `lambda_cpf`
- **Target:** `integrations/${aws_apigatewayv2_integration.lambda_cpf.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.lambda_cpf`

### Rota 4: Status Público

- **Recurso:** `aws_apigatewayv2_route.public_status`
- **Route Key:** `GET /api/v1/public/ordens-servico/{os_id}/status`
- **Autorização:** `NONE`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`

### Rota 5: Auth Me

- **Recurso:** `aws_apigatewayv2_route.auth_me`
- **Route Key:** `GET /api/v1/auth/me`
- **Autorização:** `CUSTOM`
- **Authorizer ID:** `aws_apigatewayv2_authorizer.jwt.id`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`, `aws_apigatewayv2_authorizer.jwt`

### Rota 6: Clientes

- **Recurso:** `aws_apigatewayv2_route.clientes`
- **Route Key:** `ANY /api/v1/clientes/{proxy+}`
- **Autorização:** `CUSTOM`
- **Authorizer ID:** `aws_apigatewayv2_authorizer.jwt.id`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`, `aws_apigatewayv2_authorizer.jwt`

### Rota 7: Veículos

- **Recurso:** `aws_apigatewayv2_route.veiculos`
- **Route Key:** `ANY /api/v1/veiculos/{proxy+}`
- **Autorização:** `CUSTOM`
- **Authorizer ID:** `aws_apigatewayv2_authorizer.jwt.id`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`, `aws_apigatewayv2_authorizer.jwt`

### Rota 8: Serviços

- **Recurso:** `aws_apigatewayv2_route.servicos`
- **Route Key:** `ANY /api/v1/servicos/{proxy+}`
- **Autorização:** `CUSTOM`
- **Authorizer ID:** `aws_apigatewayv2_authorizer.jwt.id`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`, `aws_apigatewayv2_authorizer.jwt`

### Rota 9: Peças

- **Recurso:** `aws_apigatewayv2_route.pecas`
- **Route Key:** `ANY /api/v1/pecas/{proxy+}`
- **Autorização:** `CUSTOM`
- **Authorizer ID:** `aws_apigatewayv2_authorizer.jwt.id`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`, `aws_apigatewayv2_authorizer.jwt`

### Rota 10: Ordens de Serviço

- **Recurso:** `aws_apigatewayv2_route.ordens_servico`
- **Route Key:** `ANY /api/v1/ordens-servico/{proxy+}`
- **Autorização:** `CUSTOM`
- **Authorizer ID:** `aws_apigatewayv2_authorizer.jwt.id`
- **Integração:** `nlb_eks`
- **Target:** `integrations/${aws_apigatewayv2_integration.nlb_eks.id}`
- **Dependência:** `aws_apigatewayv2_api.http_api`, `aws_apigatewayv2_integration.nlb_eks`, `aws_apigatewayv2_authorizer.jwt`

## Informações para Recriação no Repositório da Aplicação

### Outputs Necessários do Repositório de Infraestrutura

| Output | Descrição |
|---|---|
| `api_gateway_id` | ID do API Gateway HTTP API |
| `api_gateway_endpoint` | Endpoint URL do API Gateway |
| `api_gateway_arn` | ARN do API Gateway |
| `vpc_link_id` | ID do VPC Link |
| `nlb_dns_name` | DNS do NLB |
| `nlb_arn` | ARN do NLB |
| `lambda_authorizer_function_name` | Nome da Lambda JWT Authorizer |
| `lambda_authorizer_function_arn` | ARN da Lambda JWT Authorizer |
| `lambda_arn` | ARN da Lambda CPF Validator |

### Configurações do JWT Authorizer (para rotas protegidas)

- **Name:** `${var.environment}-jwt-authorizer`
- **Type:** `REQUEST`
- **Payload Format Version:** `2.0`
- **Identity Sources:** `["$request.header.Authorization"]`
- **TTL:** `300` segundos
- **Enable Simple Responses:** `false`

### Configurações do VPC Link (para rotas NLB)

- **Name:** `${var.environment}-vpclink`
- **Connection Type:** `VPC_LINK`
- **Security Group:** `aws_security_group.vpc_link.id`
- **Subnets:** `aws_subnet.private[*].id`

### Configurações da Integração NLB (para rotas que usam NLB)

- **Type:** `HTTP_PROXY`
- **Connection Type:** `VPC_LINK`
- **Connection ID:** `aws_apigatewayv2_vpc_link.main.id`
- **Payload Format Version:** `1.0`
- **Method:** `ANY`
- **Integration URI:** `aws_lb_listener.app.arn`
- **Timeout:** `30000` ms

### Configurações da Integração Lambda CPF (para rota /cpf)

- **Type:** `AWS_PROXY`
- **Connection Type:** `INTERNET`
- **Payload Format Version:** `2.0`
- **Integration URI:** `data.aws_lambda_function.cpf_validator.invoke_arn`
- **Timeout:** `30000` ms

## Observações

- O API Gateway tem `auto_deploy = true`, então qualquer alteração em rotas é propagada automaticamente.
- O JWT Authorizer é do tipo `REQUEST` e usa `payload_format_version = "2.0"`.
- A integração NLB usa `HTTP_PROXY` com `payload_format_version = "1.0"` (formato de requisição HTTP simples).
- A integração Lambda CPF usa `AWS_PROXY` com `payload_format_version = "2.0"` (formato de evento Lambda proxy).
