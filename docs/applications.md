# Using Enigma in applications

Enigma has durable owners for evidence and application records. Evidence
captures claims, polarity, and provenance. Application records preserve
versioned bodies by exact key.

## Choose the application boundary

| Application | Integration |
| --- | --- |
| Durable application records | Import `enigma.records.session` and `enigma.records.client`. See the [record package](../ext/enigma-records/README.md). |
| Durable evidence in a Matrix/NIL process | Import `enigma.durable.session` and `enigma.durable.client` from `ext/enigma-durable`. |
| Durable evidence in another runtime | Use a trusted adapter over the bounded JSON host protocol in [persistence.md](persistence.md). |
| Process-local evidence | Use `enigma.client`. |

## Store application records

The record owner stores UTF-8 byte arrays up to 4 MiB. A key can be absent,
present with an empty body, or present with content. Use the positive version
returned by `get` or `put` for compare-and-set replacement. Version zero is
create-only. Enumeration returns a complete batch or an empty `limit`
receipt. Owners expose the current clock floor through `describe_state()`
and hard storage ceilings through `describe_limits()`.

Use the [record package guide](../ext/enigma-records/README.md) to build the
synthetic create/reopen example and run `scripts/test-records.sh`. The local
profile has one writer, up to 2,048 live keys, and separate index, grant, body,
and aggregate byte limits. Open verifies the bodies under `max_verify_bytes`
and commits a fresh incarnation before accepting calls. Replaced bodies and
orphans still occupy disk. Goetic uses this profile on its pinned combined SDK.
[Record contract](design/ENI-0009-application-records.md) · [Consumer validation](validation.md#goetic-record-consumer--2026-11-21)

## Embed Lite for settings

Use `enigma.lite` for up to 16 text settings or small records. Its
create, open, get, put, and close calls run in the application and use
the same durable format as full records. [Lite guide](../ext/enigma-lite/README.md)

## Run the evidence example

The Matrix CLI and embedded durable evidence package share a session
implementation. The Python evidence host supports the same bounded protocol.

Select the matching complete SDK from the [development guide](development.md),
then build and exercise the package:

```sh
./scripts/test-durable-client.sh
mkdir -p data
NIL_STRICT_BOUNDS=1 ./ext/enigma-durable/build/enigma-durable-example create data/application-example
NIL_STRICT_BOUNDS=1 ./ext/enigma-durable/build/enigma-durable-example reopen data/application-example
```

The first process creates a new private store and records synthetic application
evidence. The second opens it, proves that the old grant no longer works,
explicitly admits a fresh session, discovers the persisted report, and revokes
the new grant. Both close the owner explicitly.

For an application project, add Enigma's `src` and
`ext/enigma-durable/src` directories to its NIL project `includePaths`. Import
the owner lifecycle and typed client books. Package-manager distribution is
future work; the source includes are explicit for now.

## Keep evidence admission with the host

`create_database(directory, scope)` creates only a new directory.
`open_database(directory)` opens only a valid existing store and commits
recovery before returning an owner. Connect an application client using an
explicitly installed grant. Provisioning belongs to the trusted host through
`provision_for_host`; the client has no install method.

Every typed operation takes a fresh `access_context`. The host must establish
the actual entity/session and current logical tick. An entity name or role
from an untrusted request does not establish admission. Reopening retires all
previous session grants; an application must not automatically reinstall an
old permission merely because it saved its label or numeric identifier.

The current Matrix model trusts code in its process. Public fields and a typed
client are not an isolation boundary against hostile code sharing that memory.
An Anomalous adapter must eventually supply verified admission and authority.

## Interpret the two kinds of result

Typed calls return a `durable_reply<receipt>` with `confirmed`, `receipt`, and
`failure` fields:

- `confirmed` true contains a confirmed domain receipt. Inspect `receipt.code`: `ok` means the
  operation succeeded, while `denied`, `conflict`, `limit`, or `capacity` remain
  real domain outcomes. For example, a stale expected revision is a confirmed
  conflict, not a transport failure.
- `confirmed` false contains a lifecycle/transport `failure.code` and
  `failure.outcome_unknown`. A failed
  publication can leave an effect on disk without an acknowledgement. Do not
  retry a write automatically. Close the failed owner, reopen, establish fresh
  admission, and inspect recovered state before deciding what to do next.

If a process or runtime ends without returning a reply, treat a pending write
as uncertain even though no failure record was delivered.

Accepted reads and denials can advance the security clock floor, so durable
calls preserve those changes too. Discovery and resolution also carry
completeness: an empty partial result is not proof that no evidence exists.

There is no exactly-once or durable idempotency guarantee. Expected revisions
help detect stale assumptions; they do not identify every uncertain write.

## Own and close the session

Keep one owner in one synchronous execution context, with multiple scoped
clients if needed. Close it explicitly during application shutdown. The owner
holds the single-writer lock until close. A second owner of the same store is
refused rather than queued.

If a server invokes Matrix separately for each request, keep the owner in a
long-lived storage loop or use the host protocol. Do not retain a live owner
across separate NIL invocations; the runtime closes its lock at that boundary.

Each dispatch checks runtime lock ownership. A handle retained beyond its NIL
execution, or a handle that lost its lock, cannot resume authority. Storage or
protocol failures poison the owner and prevent subsequent requests. Working
directory changes do not redirect its pinned database path.

## Current evidence limits

The local POSIX evidence profile has one store scope, 1,024 retained events,
256 retained grant rows, and a 512 KiB payload ceiling.
Assertions stop at 1,023 retained events, leaving one slot for withdrawal.
Read work ranges from 1 through 1,024, while returned evidence stays capped at
128 items. A complete scan can therefore return a partial evidence list; there
is no continuation cursor yet.

Durable admission also budgets the encoded event array at 384 KiB, with 2 KiB
reserved from assertions for withdrawal, and the encoded grant array at 64 KiB.
Long or escape-heavy data can reach byte capacity before the row ceiling. A
confirmed `capacity` response leaves the attempted evidence or grant change
absent, preserves the observed permission clock floor, and keeps the owner
usable. Compaction requires explicit scope-wide permission and gives up
historical explanations. See [ENI-0008](design/ENI-0008-bounded-capacity.md).
Multiwriter storage, general transactions, migrations, backups, native admission,
encryption, and network transport remain separate work. No release is qualified for sensitive or
production data yet.

The [application session contract](design/ENI-0007-application-sessions.md) and
[security policy](../SECURITY.md) define the implemented boundaries. The
[validation record](validation.md) identifies the tested source and SDK.
