# ADR 002: Shared Notification Service vs. Per-Team Services

**Status:** Accepted
**Date:** 2026-01-20
**Owners:** TPM (Notification Platform), Eng Leads (Checkout, Identity, Marketing)

## Context

Today, Checkout, Identity, and Marketing each maintain their own integration with a third-party email/SMS provider. This has led to three separate vendor contracts, three different opt-out/consent implementations (a compliance risk), and no unified view of notification volume or cost.

We need to decide whether to consolidate into one shared Notification Service, or formalize three separate services with shared libraries/standards instead.

## Decision

We will build **one shared Notification Service** owned by the Platform team, used by all three product teams, rather than three independently owned services.

## Consequences

**Gains:**
- Single source of truth for user opt-out/consent status — closes a real compliance gap (previously, a user could opt out via Checkout's flow and still receive Marketing SMS).
- One vendor contract and volume-based pricing tier instead of three, reducing cost.
- Centralized delivery metrics (bounce rate, delivery latency) for the first time.

**Costs:**
- **Single point of failure risk:** if the shared service has an incident, all three teams' notifications are affected, not just one. This requires a higher SLA and on-call commitment than any one team previously had, and Platform's on-call rotation had to be staffed accordingly.
- **Prioritization contention:** three teams now compete for one roadmap. We mitigated this by establishing a quarterly intake process and a defined SLA for feature requests (documented in the team's working agreement, not in this ADR).
- **Migration cost:** each team must migrate off their existing vendor integration, which is 4-6 weeks of work per team that doesn't ship user-facing value — this was the primary pushback from Marketing, whose roadmap was already committed for the quarter.
- Slower for team-specific customization; a team can't unilaterally change notification behavior without going through the shared service's API contract.

## Alternatives considered

- **Three independently owned services with a shared library.** Rejected: doesn't solve the core compliance problem (unified opt-out), since each team would still own its own data store of consent state.
- **Buy a fully managed third-party CDP (e.g., a customer engagement platform) instead of building.** Considered seriously. Rejected primarily on cost at our current volume (vendor quote was ~3.5x current spend at our scale) and on data residency requirements for the Identity team's transactional messages, which the vendor could not guarantee at the time of evaluation. This decision should be revisited if volume grows past ~10x current levels.

## Related

- ADR 001: Event-driven vs. synchronous API
- ADR 003: Rate limiting strategy
