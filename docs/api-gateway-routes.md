# Rotas do API Gateway - Documentação

Este arquivo documenta todas as rotas do API Gateway que foram implementadas no
Terraform de infraestrutura antes da separação de responsabilidades. As rotas
foram removidas do `iac-kubernetes` e devem ser recriadas no repositório da
aplicação.

## Arquitetura Atual

```text
Cliente HTTP
    │
    ▼
API Gateway HTTP API (${var.environment}-api)
    │
    ├─ Rota GET /health ──────────────────────────────┐
    ├─ Rota POST /api/v1/auth/login ──────────────────┤
    ├─ Rota GET /api/v1/public/ordens-servico/... ────┤  → VPC Link
    ├─ Rota GET /api/v1/auth/me ──────────────────────┤    │
    ├─ Rota ANY /api/v1/clientes/{proxy+} ────────────┤    ▼
    ├─ Rota ANY /api/v1/veiculos/{proxy+} ────────────┤  NLB (TCP:80)
    ├─ Rota ANY /api/v1/servicos/{proxy+} ────────────┤    │
    ├─ Rota ANY /api/v1/pecas/{proxy+} ───────────────┤    ▼
    └─ Rota ANY /api/v1/ordens-servico/{proxy+} ──────┘  Target Group
                                                            │
                                                            ▼
                                                     EKS (oficina-api)
    │
    └─ Rota POST /cpf ──────────────────────────────────────┐
                                                            ▼
                                                    Lambda CPF Validator
```

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
