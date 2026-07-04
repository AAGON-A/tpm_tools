# ADR 001: Event-Driven vs. Synchronous API for Notification Requests

**Status:** Accepted
**Date:** 2026-01-15
**Owners:** TPM (Notification Platform), Eng Lead (Platform), Eng Lead (Checkout)

## Context

Three teams (Checkout, Identity, Marketing) need to trigger notifications (email, SMS, push) to users. We need to decide how a producing team (e.g., Checkout, when an order ships) tells the Notification Service to send a message.

Two options are on the table:

1. **Synchronous REST API** — the producing team calls `POST /notifications` and waits for a response.
2. **Event-driven (pub/sub)** — the producing team publishes an event (e.g., `order.shipped`) to a message bus; the Notification Service subscribes and decides what to send.

Key constraints:
- Checkout's order-confirmation flow is latency-sensitive (user is watching a spinner).
- Marketing's campaign sends are high-volume, bursty, and not latency-sensitive.
- We want producing teams to stay decoupled from notification-specific logic (e.g., which channel, template versioning).

## Decision

We will use an **event-driven architecture** for notification triggers, with a **thin synchronous API reserved only for status/read operations** (e.g., "did this notification send," "what's the delivery status").

Producing teams publish domain events (`order.shipped`, `password.reset_requested`, `campaign.triggered`) to a shared event bus. The Notification Service subscribes to relevant events and owns the decision of channel, template, and timing.

## Consequences

**Gains:**
- Producing teams don't need to know anything about notification internals — they just emit facts about what happened in their domain.
- Marketing's bursty campaign traffic can't degrade Checkout's publish latency, since publishing an event is fire-and-forget.
- Easier to add new notification types later without changes to producing teams' code.

**Costs:**
- Debugging is harder: a "why didn't this email send" investigation now spans an event bus instead of a single request/response log.
- We need a dead-letter queue and alerting strategy for failed event processing, which is new operational surface area.
- Checkout's team initially pushed back because synchronous APIs are more familiar to debug — this required a design review to align on tracing/observability tooling (see follow-up: distributed tracing rollout, tracked separately).
- Ordering guarantees are weaker; if a user's email changes and a notification event is already queued, we need idempotency and eventual-consistency handling that a sync API wouldn't require.

## Alternatives considered

- **Fully synchronous REST for everything.** Rejected: would mean Marketing's bulk campaign sends (hundreds of thousands of requests) share the same request path as Checkout's latency-sensitive order confirmations, creating noisy-neighbor risk.
- **Per-team notification services (no shared service at all).** Rejected — covered in ADR 002.
- **Synchronous API with an internal queue behind it.** Considered as a middle ground, but this just re-implements pub/sub behind a synchronous facade while adding API versioning overhead for no real benefit, so we opted for pub/sub directly.

## Related

- ADR 002: Single shared service vs. per-team services
- ADR 003: Rate limiting strategy
