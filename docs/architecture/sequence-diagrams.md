# Diagramas de sequência

## Autenticação de uma requisição protegida

A aplicação oferece `POST /api/v1/auth/login`: verifica credenciais administrativas no código e emite JWT HS256 com `sub`, `role` e `exp`. O Gateway deste repositório não cria a rota de login. O fluxo abaixo começa com um token já emitido e só executa o authorizer se uma rota protegida for vinculada a ele. O Gateway declara source `Authorization`, TTL de 300 segundos e resposta de política IAM; a aplicação valida novamente o Bearer por `CurrentUserDep`. A ordem de leitura do Secrets Manager aparece como comportamento do handler quando seu ARN está configurado, não como prova de que a variável `jwt_secret_arn` esteja vinculada ao Secret criado. O handler consome campos de evento distintos dos esperados pela configuração `2.0`; o funcionamento ponta a ponta precisa ser verificado.

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant GW as API Gateway HTTP API
    participant Auth as Lambda authorizer JWT
    participant SM as Secrets Manager
    participant Link as VPC Link e NLB
    participant App as FastAPI no EKS
    Cliente->>GW: Requisição com Authorization Bearer
    opt Rota vinculada ao authorizer CUSTOM
        GW->>Auth: Evento REQUEST com Authorization
        Auth->>SM: Ler segredo configurado por JWT_SECRET_ARN
        SM-->>Auth: Segredo
        Auth-->>GW: Política Allow ou Deny
        alt Deny
            GW-->>Cliente: Requisição rejeitada
        end
    end
    opt Requisição autorizada e rota integrada ao NLB
        GW->>Link: HTTP_PROXY por VPC Link
        Link->>App: Requisição HTTP encaminhada
        App->>App: CurrentUserDep decodifica e valida JWT
        alt JWT válido
            App-->>Link: Resposta da API
            Link-->>GW: Resposta
            GW-->>Cliente: Resposta
        else JWT inválido ou expirado
            App-->>Link: 401
            Link-->>GW: 401
            GW-->>Cliente: 401
        end
    end
```

[Fonte Mermaid](../diagrams/authentication-sequence.mmd).

## Abertura de ordem de serviço

O endpoint confirmado na FastAPI é `POST /api/v1/ordens-servico` (sem barra final no decorator); exige `CurrentUserDep` e recebe IDs de cliente, veículo, serviços e peças. A migration e o repositório ORM mostram persistência em PostgreSQL quando `DATABASE_URL` aponta ao RDS. O caso de uso busca cliente e veículo, busca serviços e peças informados, calcula o orçamento, passa por `DIAGNOSTICO` até `AGUARDANDO_APROVACAO`, salva ordem e itens e emite `ServiceOrderCreated`. IDs de serviço ou peça não encontrados são ignorados no cálculo atual; o vínculo entre cliente da ordem e proprietário do veículo não é verificado no caso de uso nem por constraint composta no banco. O repositório faz commits separados para ordem e itens, logo não há atomicidade de toda a criação. O código da abertura não usa CPF nem invoca a Lambda; a validação CPF acontece no cadastro de cliente.

```mermaid
sequenceDiagram
    autonumber
    actor Cliente
    participant GW as API Gateway HTTP API
    participant Auth as Lambda authorizer JWT
    participant Link as VPC Link e NLB
    participant App as FastAPI no EKS
    participant UC as AbrirOsUseCase
    participant DB as PostgreSQL no RDS
    participant NR as New Relic
    Cliente->>GW: POST /api/v1/ordens-servico com Bearer e IDs
    opt Rota protegida vinculada ao authorizer
        GW->>Auth: Validar JWT HS256
        Auth-->>GW: Allow ou Deny
    end
    opt Rota integrada ao NLB e autorizada
        GW->>Link: HTTP_PROXY via VPC Link
        Link->>App: Encaminhar requisição
        App->>App: Validar JWT em CurrentUserDep e payload Pydantic
        App->>UC: AbrirOsDTO
        UC->>DB: Buscar cliente e veículo por ID
        DB-->>UC: Cliente e veículo ou ausência
        alt Cliente ou veículo ausente
            UC-->>App: Erro de domínio
            App-->>Link: 404
            Link-->>GW: 404
            GW-->>Cliente: 404
        else Ambos encontrados
            UC->>DB: Buscar serviços e peças informados por ID
            DB-->>UC: Cadastros encontrados
            UC->>UC: Calcular orçamento e mudar status para AGUARDANDO_APROVACAO
            UC->>DB: Salvar ordem e itens em commits separados
            DB-->>UC: Ordem persistida
            UC->>NR: Evento ServiceOrderCreated se agente APM ativo
            UC-->>App: OrdemServicoResponseDTO
            App-->>Link: 201 e ordem criada
            Link-->>GW: 201
            GW-->>Cliente: 201 e ordem criada
        end
    end
```

[Fonte Mermaid](../diagrams/service-order-sequence.mmd). O Gateway deste repositório define as integrações, mas não contém `aws_apigatewayv2_route`. A antiga [lista de rotas](../api-gateway-routes.md) usa singular `/api/v1/ordens-servico/{proxy+}` e informa que foi removida; não confirma a rota de criação plural hoje. Assim, a passagem pelo Gateway no segundo diagrama é condicionada à configuração efetiva de uma rota compatível em outro lugar.

Fontes principais: `terraform/api_gateway.tf`, `terraform/lambda/authorizer/index.py`; no repositório da aplicação, `src/api/routes/{auth,ordem_servico}_routes.py`, `src/api/dependencies.py`, `src/application/usecases/ordem_servico/abrir_os.py`, `src/infrastructure/database/repositories/ordem_servico_repository.py`.
