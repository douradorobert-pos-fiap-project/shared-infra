# RFC-002 — Banco relacional PostgreSQL no RDS

**Status:** Adotada na configuração AWS; SQLite é padrão local de desenvolvimento da aplicação.

## Contexto

A migration da Oficina define clientes, veículos, ordens e itens com FKs, índices, unicidade e preços `numeric(10,2)`. O banco é provisionado em `database-infra` na VPC compartilhada, separado deste repositório.

## Problema

Persistir entidades relacionadas com identidade estável e integridade referencial, mantendo a operação do motor de banco fora dos pods da aplicação.

## Alternativas consideradas

- SQLite: aparece como valor padrão em `settings.py` para execução local; não é a instância configurada para AWS.
- PostgreSQL autogerido no EKS/EC2: preservaria o modelo relacional, mas exigiria operação própria de armazenamento, backups e upgrades.
- Banco não relacional: demandaria remodelar FKs e consultas implementadas; não há evidência de protótipo ou benchmark.

## Proposta adotada

Amazon RDS PostgreSQL com subnet group privado, acesso TCP/5432 dentro da VPC, `gp3`, backups automáticos configuráveis e upgrades menores automáticos. A aplicação usa SQLAlchemy/Alembic e `DATABASE_URL` injetada no Deployment.

## Justificativa

PostgreSQL atende FKs, unicidade e tipos monetários da migration; RDS reduz a manutenção do servidor e integra o banco à VPC/EKS. Transações são suportadas pelo motor, mas a rotina atual de salvar ordem e itens usa commits separados.

## Consequências positivas

Fica possível validar a existência de pais por FK, indexar referências e manter backups automáticos. A aplicação pode migrar o esquema por Alembic.

## Trade-offs

O RDS atual declara `multi_az = false`, `deletion_protection = false`, retenção padrão de um dia e snapshot final omitido por padrão. Não há FK dos itens para os catálogos nem constraint de proprietário do veículo na ordem. O custo e o limite de conexão do RDS exigem gestão operacional, sem números medidos no repositório.

**Evidências:** `../database-infra/terraform/{main,variables}.tf`, `../tech-challenge-fiap/migrations/versions/001_initial_schema.py`, `../tech-challenge-fiap/src/infrastructure/database/`.
