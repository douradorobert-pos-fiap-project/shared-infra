# ADR-004 — PostgreSQL gerenciado pelo Amazon RDS

**Status:** Adotada no repositório de banco da solução.

## Contexto

A migration da aplicação declara sete tabelas relacionais, com FKs entre cliente, veículo, ordem e itens, além de índices e unicidade.

## Decisão

Usar engine PostgreSQL em RDS privado na VPC compartilhada, acessado pela aplicação via `DATABASE_URL`. O esquema é gerido com Alembic/SQLAlchemy no repositório da aplicação.

## Justificativa

PostgreSQL fornece integridade referencial, `numeric(10,2)` e transações para o modelo implementado; RDS cuida da instância, backups e upgrades menores configurados.

## Consequências

O banco permanece fora do ciclo de vida dos pods. A configuração atual é Single-AZ, sem proteção de exclusão; disponibilidade Multi-AZ não foi adotada. A rotina de abertura não é atômica entre ordem e itens por usar commits separados. FKs dos itens para peças/serviços e consistência proprietário do veículo não estão implementadas.

## Alternativas consideradas

- SQLite local: já é o padrão da aplicação para desenvolvimento, mas não o banco configurado na AWS.
- PostgreSQL autogerido: aumentaria responsabilidade por armazenamento e manutenção.

**Evidências:** `../database-infra/terraform/main.tf`, `../tech-challenge-fiap/migrations/versions/001_initial_schema.py`, [modelo relacional](../architecture/database-design.md).
