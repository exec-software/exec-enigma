# Query and operation surface

Status: typed evidence operations are implemented; a textual query parser is
not implemented.

Enigma's canonical surface is an operation model that preserves evidence,
provenance, authority, historical revision, and completeness. It is not
predetermined to be relational, document-oriented, SQL, or NoSQL. Storage
structure and human syntax should serve that model instead of selecting the
semantics by convention.

## Working typed surface

The companion [Matrix client](../../ext/enigma-client/README.md) lives under
`ext/enigma-client`, outside the framework's core standard library. It exposes
`support`, `oppose`, `resolve`, `inspect`, `withdraw`, `compact`, and `discover`, plus a discoverable
surface descriptor. Requests pass typed propositions and explicit parameters;
agents do not need to synthesize query strings.

A proposition is the exact triple `(subject, relation, object_value)`. Support
and opposition are separate attributable evidence, not overwriting assignments.
Different values are not automatically contradictory. The current value type
is bounded text; richer values and relation semantics remain future work.

Resolution supplies an explicit snapshot, work budget, and evidence-list budget.
Revision `0` is a real empty view; `-1` requests latest. Complete scans distinguish
`unknown`, `supported`, `contradicted`, and `contested`. Work exhaustion yields
`incomplete` rather than a final answer. A fully scanned answer can have an
incomplete evidence list; `evidence_complete` reports that separately.

Writes accept an expected revision so an agent can detect stale assumptions.
Withdrawals append a correction event and preserve prior snapshots. Withdrawal
and inspection also check grant work limits and can return `limit` without
returning evidence. See [ENI-0001](ENI-0001-evidence-and-authority.md) for the
complete operation and authority contract.

Discovery accepts exact-or-any selectors for the proposition's three fields,
so a caller can explore a subject or relation without guessing a complete
triple. In Matrix, `Option.None` means any and `Option.Some holding text` means
exact text. Characters such as `*` remain literal data. The durable protocol
uses JSON `null` and strings for the same distinction.

`discover` returns active reports with full provenance, newest ID first, at
one explicit snapshot. It reports scan and output completeness separately,
like resolution. `matched` counts observed reports rather than propositions;
it is a lower bound when the scan is incomplete. Reports can disagree, and
discovery supplies no truth verdict. Current scoped read authority applies,
including to old snapshots. See [ENI-0006](ENI-0006-bounded-evidence-discovery.md)
for the work, retention, and failure contract.

Compaction explicitly reclaims an assertion together with its withdrawal,
retaining unwithdrawn evidence and every issued identifier. Its receipt reports
the reclaimed event count and the retained-history horizon. A resolve below that
horizon reports `incomplete`, while revision `0` and views at or above the
horizon remain exact when fully scanned. Inspection of a reclaimed assertion
returns `not_found`. See [ENI-0005](ENI-0005-evidence-retention.md).

This is scope-wide maintenance that can discard another holder's retracted
history. It requires separate right `16`; withdraw-own right `4` alone does
not authorize compaction. The client and any future text parser must preserve
that distinction rather than infer maintenance authority from a write grant.

## Named views in Matrix

The first named read-only view is `resume_work` in `enigma.work.views`.
It takes a connected record client, current caller context, a handoff key,
and explicit listing limits. It returns a typed handoff with its freshness
check from one observed manifest generation.

`describe_resume_work()` exposes the view name and version, the record
operations it calls, and its resource ceilings. The trusted application
chooses which views to expose. Use ordinary Matrix calls to invoke this view.
The `begin view` text grammar and guarded write commands remain design
directions. See the [work package](../../ext/enigma-work/README.md).

## Future Matrix-inspired text

A human-readable language should borrow Matrix's named inputs, explicit types,
word operators, and visible block boundaries. It must compile into the same
typed operations used by the client, with the same authority and resource
checks. The language should expose evidence and completeness directly rather
than conceal disagreement behind a single selected value.

No concrete text grammar is standardized in this slice. Before implementing
one, define acceptance fixtures for a bounded expression of a proposition,
support or opposition with source attribution, a historical evidence view, and
an explicit work/output budget. Do not accept arbitrary Matrix programs as
queries.

The future parser must keep data bindings separate from language structure,
reject ambiguous or unknown constructs, bound input and nesting, and return
structured source errors. A bound value must not introduce identifiers or
operations. Natural-language plausibility must not select permissions or
silently repair a request into a different effect.

## One authority path

Identity and authority come from the host, outside operation text and data
bindings. Enigma follows the separation in Anomalous's [identity and authority
design](https://github.com/exec-software/exec-anomalous/blob/87e365dadac72a481b03cfe175b06e0129dc6c1d/docs/architecture/identity-and-authority.md).
A future native adapter must establish the live session and applicable sigils;
the current embedded engine uses explicit trusted-host fixtures.

Neither textual requests nor the client can authorize themselves. Current
grants apply to historical views too. The host supplies fresh logical-tick
context per dispatch; client snapshots do not establish realtime freshness.
Current public Matrix class fields are not isolation from hostile same-process
code. The [durable host](../persistence.md) commits persistence and revocation
state through this same operation model; direct client calls remain volatile.
Authentication, native admission, network transport, inference, and causal
dependencies remain separate work.
