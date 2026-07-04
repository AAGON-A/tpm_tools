# API Architecture Decision Records — Notification Service

**A set of real-world-style Architecture Decision Records (ADRs), an OpenAPI spec, and a system diagram for a fictional but realistic system: a shared Notification Service used by 3 product teams.**

## Why this exists

TPMs are rarely the ones writing production code — but they're often the ones in the room when architecture decisions get made, and they need to be able to read a system diagram, understand tradeoffs (REST vs. event-driven, sync vs. async, build vs. buy), and write decisions down so they don't get relitigated every quarter.

This repo simulates that: a scenario where **Checkout**, **Identity**, and **Marketing** teams all need to send notifications (email, SMS, push) to users, and instead of each team building their own, a shared Notification Service is proposed.

## Scenario

> Three product teams (Checkout, Identity, Marketing) each need to send transactional and marketing notifications to users across email, SMS, and push. Currently each team has its own ad hoc integration with a third-party provider, leading to inconsistent rate limiting, no unified opt-out handling, and duplicate vendor contracts. A shared Notification Service is proposed.

## Contents

| File | What it is |
|---|---|
| [`adrs/001-event-driven-vs-sync-api.md`](adrs/001-event-driven-vs-sync-api.md) | Should teams call a sync REST API or publish events? |
| [`adrs/002-single-tenant-vs-shared-service.md`](adrs/002-single-tenant-vs-shared-service.md) | Should this be one shared service or one per team? |
| [`adrs/003-rate-limiting-strategy.md`](adrs/003-rate-limiting-strategy.md) | How to prevent one team's traffic spike from starving others |
| [`diagrams/architecture-overview.svg`](diagrams/architecture-overview.svg) | High-level system diagram |
| [`openapi/notification-service.yaml`](openapi/notification-service.yaml) | OpenAPI 3.0 spec for the resulting API |

## How to read an ADR here

Each ADR follows the same lightweight format:
- **Status** — proposed / accepted / superseded
- **Context** — what problem forced this decision
- **Decision** — what we chose
- **Consequences** — what we gained and what we gave up (every real decision has a cost)
- **Alternatives considered** — what else was on the table and why it lost

## Why this matters for a TPM role

Writing an ADR is a TPM skill even when you didn't design the system: it means you understood the tradeoffs well enough to explain them to both engineers (who want technical rigor) and stakeholders (who want to know "why will this take 6 weeks and not 2"). The "Consequences" section in each ADR here is deliberately honest about downsides — a TPM who only writes upside isn't trusted for long.
