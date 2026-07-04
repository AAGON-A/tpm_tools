# ADR 003: Rate Limiting Strategy for Shared Notification Service

**Status:** Accepted
**Date:** 2026-02-03
**Owners:** TPM (Notification Platform), Eng Lead (Platform)

## Context

With a shared Notification Service (ADR 002) consuming events from three teams (ADR 001), we need a way to prevent one team's traffic from starving another's. The specific failure mode we're designing against: Marketing runs a large promotional campaign (e.g., 500K SMS in an hour), and Checkout's time-sensitive order-confirmation emails get delayed behind it in the same processing queue.

## Decision

We will implement **per-team quota-based rate limiting at the event-consumption layer**, with three priority tiers:

- **Tier 1 (transactional, e.g., order confirmations, password resets):** no rate limit, processed first.
- **Tier 2 (account-related, e.g., security alerts):** high priority, soft cap during extreme load.
- **Tier 3 (marketing/campaign):** hard quota per hour, configurable per team, processed only after Tier 1/2 queues are clear.

Each team's events are tagged with a tier at publish time (part of the event schema), not decided by the Notification Service after the fact — this keeps the responsibility with the team that best knows the urgency of their own message.

## Consequences

**Gains:**
- Checkout's transactional emails are protected from Marketing's burst traffic by design, not by hoping queues stay short.
- Marketing gets a predictable, contractually-agreed hourly quota instead of "best effort," which is actually an improvement over the previous ad hoc vendor integration where large sends occasionally got throttled unpredictably by the vendor itself.

**Costs:**
- Marketing must plan large sends around their quota, which requires coordination for major campaign moments (e.g., a flash sale) — we added a "quota burst request" process for pre-planned large sends, submitted 48 hours in advance.
- Mis-tagging a message's tier (e.g., a team marking a marketing message as Tier 1 to skip the queue) is a possible failure mode. We mitigated this with a lightweight audit: Platform reviews tier distribution weekly and flags anomalies, rather than building a fully automated enforcement system, which was judged not worth the engineering cost at current scale.
- Adds one more piece of schema (the tier field) that every producing team must correctly set, which is a small but real integration burden during onboarding.

## Alternatives considered

- **Global rate limit only (no per-team tiers).** Rejected: doesn't solve the actual problem, since the goal is protecting transactional traffic specifically, not limiting total throughput.
- **Separate infrastructure per tier (e.g., dedicated queue clusters).** Considered for stronger isolation guarantees. Rejected for now as premature — the quota-based approach solves the known failure mode at current volume without the added operational cost of managing multiple queue clusters. Flagged as a candidate if Tier 3 volume grows significantly.

## Related

- ADR 001: Event-driven vs. synchronous API
- ADR 002: Shared Notification Service vs. per-team services
