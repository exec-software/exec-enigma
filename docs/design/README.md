# Enigma design

Enigma tests an evidence-oriented database model for people and agents. The
working first slice preserves competing reports, their provenance, and the
historical view before a withdrawal. It does not commit the engine to relational
tables, document collections, or an existing SQL/NoSQL category.

The benefit to evaluate is concrete: an agent can retain disagreement, inspect
what supports an answer, and distinguish an incomplete investigation from an
absence of evidence. This is a design hypothesis, not a claim that evidence or
temporal database concepts are new.

## Implemented slice

[ENI-0001: Evidence views under explicit authority](ENI-0001-evidence-and-authority.md)
defines evidence behavior. [ENI-0002: Durable state and fail-closed recovery](ENI-0002-durable-state-and-recovery.md)
defines the persistence host and restart contract.
[ENI-0003: The Matrix durable host](ENI-0003-matrix-durable-host.md) decides how
the Python placeholder host is retired.
[ENI-0004: Authority capacity across restarts](ENI-0004-authority-capacity.md)
decides how retired grants are reclaimed without recycling an identifier.
[ENI-0005: Evidence retention](ENI-0005-evidence-retention.md) gives the event
log the same treatment, reclaiming retracted evidence on request.
[ENI-0006: Bounded evidence discovery](ENI-0006-bounded-evidence-discovery.md)
adds exact-or-any patterns over active reports without requiring a known triple.
[ENI-0007: Durable application sessions](ENI-0007-application-sessions.md)
defines importable ownership, typed durable calls, and uncertain-failure handling.
[ENI-0008: Bounded checkpoint capacity](ENI-0008-bounded-capacity.md)
separates retained events, read work, reply bounds, and durable byte admission.

| Area | Current behavior |
| --- | --- |
| Evidence | Exact text propositions with independently attributable support and opposition. |
| Discovery | Exact-or-any selectors return active reports with provenance, a pinned snapshot, and separate scan/output completeness. |
| History | Assertions and withdrawals append events; as-of reads preserve prior views. |
| Resolution | `unknown`, `supported`, `contradicted`, or `contested` after a complete scan; `incomplete` when work runs out. |
| Bounds | 1,024 retained events per store, 1,023 assertion admission, work through 1,024 events, 128-item replies, and separate durable byte budgets. An invoked compaction reclaims retracted evidence; a view below the resulting horizon answers `incomplete`. |
| Authority | Trusted-host entity/session grants with exact audience, scope, rights, logical expiry, attenuation, and live ancestor revocation. |
| Client | Typed operations and a discoverable surface under [`ext/enigma-client`](../../ext/enigma-client/README.md), outside `nil.std`. |
| Persistence | Matrix checkpoint codec and validated recovery, with POSIX host locking, private files, atomic replacement, and sync-before-receipt ordering. |
| Restart authority | Retire every old session grant and reclaim its row, retaining the identifier counter, retirement high-water mark, and clock floor; commit a fresh incarnation before `ready`. |

Each store has independent IDs, revisions, capacity, and work budgets. A failed
write does not advance its revision. Current authority is required even for an
old snapshot. Withdrawal and inspection honor grant work limits and return a
structured `limit` response when the required scan is too large.

The implementation is Matrix, configured through NILData. The canonical surface
is the typed evidence operation model. No text query parser, inference system,
causal dependency model, or network transport exists. Direct
`enigma.client` use remains volatile; durable receipts come through a POSIX
storage host or the importable session defined in ENI-0007.

## Application records

The separate record profile stores exact UTF-8 bodies up to 4 MiB, with
compare-and-set versions, complete key enumeration, and separate byte authority.
Goetic uses the profile on its pinned combined development SDK.
[ENI-0009](ENI-0009-application-records.md) · [Consumer validation](../validation.md#goetic-record-consumer--2026-11-21)

## Lite record stores

Lite exposes an embedded settings API with smaller key and byte limits
over the durable record format. [ENI-0012](ENI-0012-lite-records.md)

## Work handoffs

The Matrix companion records handoffs and earlier attempts as ordinary
application records. It checks whether named input versions changed between
sessions under current authority. [ENI-0010](ENI-0010-work-handoffs.md)

## Authority direction

Follow Anomalous's separation of entity identity, admitted session, and scoped
sigil authority, as described in its [identity and authority design](https://github.com/exec-software/exec-anomalous/blob/87e365dadac72a481b03cfe175b06e0129dc6c1d/docs/architecture/identity-and-authority.md)
and [ADR 0040](https://github.com/exec-software/exec-anomalous/blob/87e365dadac72a481b03cfe175b06e0129dc6c1d/docs/adr/0040-separate-entity-identity-authentication-and-authority.md).
Human and agent requests share the same operation and policy path. An entity
name, an asserted purpose, or an administrator label cannot grant authority.

The working registry uses trusted-host fixture grants and supplied logical
ticks. It does not authenticate entities or obtain native task/channel/session
provenance. The host must establish fresh context for each dispatch; a copied
client context is not a live clock. Matrix class fields are public, so direct
same-process memory access is outside the API policy boundary. There is no
hostile-process isolation, realtime-expiry guarantee, or native Anomalous adapter.
See the [security policy](../../SECURITY.md).

The durable path retains evidence and security state together. Opening a store
retires and reclaims every old session grant, preserves issued counters and
the retirement mark, and commits a fresh random incarnation before admitting requests. New authority
requires explicit re-admission; old-incarnation requests receive a fixed denial.
Corruption or missing canonical state fails closed instead of restoring an older
permission snapshot. An identifier is never recycled. Recovery reclaims the
rows it retires, so the 256-row ceiling no longer bounds every grant a database
will ever issue. It still counts rows revoked in the current session. A reclaimed
identifier is refused as revoked rather than as one that never existed.
Exhausting the retained-row ceiling fails closed. See
[ENI-0004](ENI-0004-authority-capacity.md).

Durability assumes a trusted owner and storage ancestry plus a local POSIX
filesystem honoring sync, atomic rename, and advisory locks. A coherent older
checkpoint restored outside the protocol cannot be detected without separately
trusted monotonic state. The current recovery path prevents saved session
authority from being restored; it does not prove general anti-rollback, durable
replay/idempotency accounting, or hardware power-cut behavior. See [the
persistence guide](../persistence.md).

## Next questions and milestones

1. **Native authority integration:** consume verified Anomalous admission and
   installed sigils through an explicit adapter. Define request/effect binding,
   replay handling, fresh session incarnations, and the trusted clock boundary.
2. **Richer evidence semantics:** evaluate typed values, causal dependencies,
   derived conclusions, and changes that invalidate them. Define how authority
   and provenance propagate before exposing cross-scope reasoning.
3. **Persistence beyond the bounded checkpoint:** authority reclamation
   ([ENI-0004](ENI-0004-authority-capacity.md)) and evidence retention
   ([ENI-0005](ENI-0005-evidence-retention.md)) are done. Define migrations,
   backup and restore, which is where history wanted after compaction has to
   come from, durable replay/idempotency, externally anchored rollback
   detection, and broader filesystem qualification.
4. **Human language surface:** design bounded Matrix-inspired syntax that compiles
   into the same typed operations and authority checks. A parser must not execute
   arbitrary Matrix or grant authority from text.
5. **Evaluation:** measure workloads involving competing evidence, corrections,
   historical explanations, and constrained agent activity. Compare usefulness,
   correctness, and cost with reproducible baselines.

Package-manager distribution of the client is deferred. Broader storage layouts,
concurrency, query indexes, transport encoding, encryption dependencies, and
compatibility policy remain open. Choose those mechanisms to support useful,
testable behavior; do not infer them from an architectural label.

See [query surface direction](query-language.md) for the shared operation model.
