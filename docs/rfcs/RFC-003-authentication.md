# RFC-003 — Autenticação e autorização com JWT

**Status:** Componentes implementados; operação ponta a ponta condicionada à configuração das rotas e do authorizer.

## Contexto

A FastAPI expõe login que verifica credenciais administrativas definidas no código e emite JWT Bearer HS256 com `sub`, `role` e `exp`. Endpoints protegidos usam `CurrentUserDep` para decodificar o token. Este repositório cria API Gateway HTTP API, Lambda authorizer `REQUEST` e Secret no Secrets Manager.

## Problema

Impedir acesso sem token válido nas rotas protegidas e deixar a aplicação identificar o usuário da requisição.

## Alternativas consideradas

- Validar somente na aplicação: eliminaria o filtro no Gateway, mas os endpoints ainda precisariam de `CurrentUserDep`.
- Usar authorizer gerenciado OIDC/Cognito: não há identidade desse tipo configurada no código.
- Usar sessões de servidor: exigiria persistência e fluxos diferentes dos tokens implementados.

## Proposta adotada

Login na aplicação; token JWT HS256 em `Authorization: Bearer`. Para rotas que forem vinculadas ao authorizer, API Gateway chama a Lambda; o handler consulta o segredo pelo ARN em `JWT_SECRET_ARN`, valida assinatura/expiração e devolve política Allow/Deny com principal `sub`. A FastAPI revalida JWT por `CurrentUserDep`. O Gateway não cria rotas neste repositório, logo a associação a `CUSTOM` deve ser feita onde as rotas forem geridas.

## Justificativa

O token é autocontido e os mecanismos já existem em ambos os lados da entrada. O Gateway pode recusar uma requisição antes do VPC Link quando sua rota estiver protegida; a aplicação mantém sua própria checagem.

## Consequências positivas

JWT permite carregar `sub`/`role` e expiração; o segredo fica em Secrets Manager para o authorizer; a API retorna 401 quando o JWT não passa na validação local.

## Trade-offs

É necessário sincronizar `settings.JWT_SECRET` da aplicação com o segredo lido pelo authorizer. O Secret criado aqui não é vinculado automaticamente à variável `jwt_secret_arn`. A configuração Gateway usa evento de authorizer `2.0`, enquanto o handler lê `authorizationToken` e `methodArn`; não há prova de compatibilidade. O cache do authorizer dura 300 s; não há revogação de token individual documentada. O login administrativo usa credenciais definidas no código, sem cadastro de usuários no banco.

**Evidências:** `terraform/{api_gateway,lambda_authorizer,secrets}.tf`, `terraform/lambda/authorizer/index.py`, `../tech-challenge-fiap/src/{api/routes/auth_routes.py,api/dependencies.py,infrastructure/auth/jwt_handler.py}`.
