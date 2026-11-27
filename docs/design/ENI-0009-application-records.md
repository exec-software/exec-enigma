# ENI-0009: Application records with immutable bodies

Implemented and used by Goetic on Linux with its pinned combined development
SDK. See the [validation record](../validation.md) for the tested scope.

## Record model

An application record has a key, exact UTF-8 body bytes, and a positive
version. Goetic keeps its domain history inside each aggregate body. Enigma
stores the latest body and provides compare-and-set replacement and complete
key enumeration.

The record profile has its own durable format and authority. Evidence stores
keep their evidence semantics and APIs. Each profile has its own owner, and
operations cannot commit across them.

Bodies are strict UTF-8 byte arrays. Enigma preserves embedded NUL, whitespace,
line endings, and different Unicode spellings. The engine validates encoding
and leaves application formats and schemas to the application. Keys are 1–256
strict UTF-8 bytes without NUL. Key order is unsigned UTF-8 byte order. Slashes,
backslashes, dots, and wildcard characters are literal key data. The engine
uses a fresh opaque body identifier for each put and never derives a filesystem
path from a key.

## Resource limits

| Resource | Ceiling |
| --- | --- |
| Live keys per store | 2,048 |
| Bytes per key | 256 |
| Bytes per body | 4 MiB |
| Bytes across referenced bodies | 1 GiB |
| Encoded record index | 384 KiB |
| Retained grants | 256 rows and 64 KiB encoded |
| Manifest payload and integrity envelope | 512 KiB and 1 MiB respectively |
| Complete enumeration | 2,048 entries and 512 KiB of metadata |
| Record sequence and manifest generation | 2,147,483,646 each |

The index can reach its byte ceiling before its key ceiling. The byte budget
for enumeration measures the compact JSON encoding of an array of
`[key, version, byte_length]` rows, including brackets, separators, and escape
characters. The typed reply contains the rows as a batch. Capacity and limit
checks return whole-operation refusals.

The live-byte ceiling counts only referenced bodies. Replacements and
interrupted puts can leave unreferenced files, and the engine currently keeps
them. Disk provisioning must account for those files. Safe, bounded reclamation
requires its own reachability and durability contract.

## Matrix API

Use the `enigma.records.session` and `enigma.records.client` books. The
[package guide](../../ext/enigma-records/README.md) shows the project includes
and a synthetic create/reopen example.

| Public call | Return |
| --- | --- |
| `create_record_database(directory, scope)` | `record_open_result` |
| `open_record_database(directory, max_verify_bytes)` | `record_open_result` |
| `record_owner.close()` | `closed` or `lock_error` |
| `record_owner.describe_limits()` | `record_limits` |
| `record_owner.describe_state()` | `record_state_view` |
| `provision_record_host(owner, entity, session_id, actions, expires, limits, tick)` | `record_reply<record_grant_receipt>` |
| `connect_records(owner, grant_id)` | `record_client` |
| `record_client.get(caller, key, max_body_bytes)` | `record_reply<record_get_receipt>` |
| `record_client.put(caller, key, content, expected_version)` | `record_reply<record_put_receipt>` |
| `record_client.put_checked(caller, key, content, expected_version, guards)` | `record_reply<record_put_receipt>` |
| `record_client.list_keys(caller, max_keys, max_metadata_bytes, max_scan_keys)` | `record_reply<record_list_receipt>` |
| `record_client.revoke(caller)` | `record_reply<record_grant_receipt>` |
| `record_client.delegate(caller, entity, session_id, actions, expires, limits)` | `record_reply<record_grant_receipt>` |

`record_open_result` contains `code`, `outcome_unknown`, and `owner`.
`created` and `ready` return active owners. Other outcomes disable the owner
and release acquired locks.

`describe_limits()` returns `max_keys`, `max_key_bytes`, `max_body_bytes`,
`max_live_bytes`, `max_index_bytes`, `max_grants`, `max_grant_bytes`,
`max_manifest_bytes`, `max_envelope_bytes`, and `max_list_metadata_bytes`.
`describe_state()` checks current lock ownership and returns `code`,
`database_id`, `scope`, `incarnation`, `generation`, and `clock_floor`.
A trusted host can establish its logical time from the recovered floor before
it admits a fresh session.

`record_reply<T>` contains `confirmed`, `receipt`, and `failure`.
`record_failure` contains `code` and `outcome_unknown`. A confirmed response
provides a domain receipt and clears failure metadata. Successful receipts
have `code = ok`. Confirmed refusals, such as `conflict`, `limit`, and
`capacity`, clear record metadata. An unconfirmed call can have an uncertain
effect if manifest publication was attempted.

| Receipt | Fields |
| --- | --- |
| `record_get_receipt` | `code`, `found`, `content`, `version`, `byte_length` |
| `record_put_receipt` | `code`, `version`, `byte_length` |
| `record_list_receipt` | `code`, `complete`, `entries`, `generation` |
| `record_grant_receipt` | `code`, `grant_id` |

`get` returns `found = false`, empty content, and version zero for an absent
key. A persisted empty body returns `found = true` and a positive version.
Read capacity is checked before the engine loads the body. Corruption returns
an unconfirmed failure and disables the owner.

`put` requires a version precondition. Use `expected_version = 0` to create
an absent key or the exact current version to replace a body. A stale
precondition returns `conflict` without revealing the existing body or
version. Each successful put increments the store's record sequence, including
a replacement with identical bytes. Use the returned version since another
key can consume intervening versions. The profile has no delete or historical
body lookup.

`put_checked` adds one to sixteen exact input versions to a one-record write.
It requires current read and write authority and checks the input and
destination versions under the same owner lock.
[Guarded write contract](ENI-0011-guarded-record-writes.md)

`list_keys` returns ordered entries from one manifest generation. Each
`record_key_entry` has `key`, `version`, and `byte_length`. Use
`record_key_batch.count()` and its checked `get(index)` to inspect entries.
When the list exceeds any authorized request budget, the receipt is
`limit` with an empty batch and `complete = false`. Independent gets can
observe later generations. Compare the returned versions to detect changes.

## Authority and owner lifetime

Record authority uses read bit `1`, write bit `2`, list bit `4`, and delegate
bit `8` in a distinct grant profile. The grant binds entity, session,
audience, scope, expiry, and revocation ancestry. Its `record_access_limits`
fields are `max_read_bytes`, `max_write_bytes`, `max_scan_keys`,
`max_list_keys`, and `max_list_metadata_bytes`. Delegation can only narrow
rights and every limit. Revocation immediately denies later requests through
descendant grants. The engine checks current authority before key lookup or
body access.

The trusted host provisions authority. Each client call takes fresh, trusted
`access_context` including a logical tick. The caller's tick cannot roll back
below the committed floor. A read or refusal that raises the floor commits the
change before returning a confirmed reply. An application such as Goetic can
apply its actor policy before invoking Enigma with service authority.

Keep an owner in one synchronous NIL execution. The owner holds one exclusive
advisory writer lock, checks its runtime token on every dispatch, and disables
every alias on close. Runtime cleanup can retire a token when the invocation
ends. A stale object cannot use that lock afterward. Data and class fields
belong to trusted code in the same process. Authentication and native
Anomalous admission are separate work.

## Publication and recovery

The owner uses a private store directory with `.lock`, `manifest.json`, and
a private `objects/` directory. The canonical manifest uses
`enigma.records.v1` inside the checked integrity envelope. It contains
identity, incarnation, generation, index, byte totals, record sequence and
authority, including the issued grant counter, revocation state and clock
floor. The index stores ordered rows of key, version, body length, opaque
identifier and SHA-256 digest in pages of up to 32 rows. Every nonfinal page
is full. This bounds the work of a codec that reparses encoded values. The
owner still checks the full manifest per call and publishes a complete
successor on each mutation or security clock change. Bodies use separate
bounded files, so they never enter NILData's 1 MiB value boundary.

For a put, the engine checks authority, preconditions, and capacity, then
prepares the candidate manifest. It durably writes the new body with
no-clobber publication and syncs its directory. It next publishes and syncs
the canonical manifest, then returns the confirmed receipt. A failed body
write can leave an unreferenced file. It cannot advance the canonical index.
A failure from attempted manifest publication has an unknown outcome. Actual
storage failures poison the owner, and confirmed domain refusals keep it
usable. The caller must close, reopen and inspect state before deciding
whether to repeat an uncertain write.

Opening holds the lock, validates the manifest and authority together, and
reads every referenced body to check private file metadata, exact length,
digest, and UTF-8. Set `max_verify_bytes` to the maximum total body bytes the
host is willing to verify on open. Insufficient budget returns `limit`
before the body scan. Successful open has paid the full scan cost. Each
subsequent successful found get verifies its body again. Missing or corrupt
canonical files and unsafe paths fail closed. Orphans and older bodies are
outside the recovery candidate set.

Recovery retires all loaded grants and reclaims their rows. It preserves the
clock floor and issued grant counter with the retirement mark. The owner
durably publishes a fresh incarnation before reporting `ready`. Old sessions
require explicit re-admission. Creation exclusively makes a new store and
syncs the storage parent before reporting `created`.

This contract assumes a trusted storage owner and ancestry, co-operating
writers, and a local POSIX filesystem honoring locks, atomic rename and sync.
Bodies and manifests are plaintext. The digest detects corruption. Backup
and restore tooling, externally anchored rollback detection, native
admission, encryption, release SDKs, and hardware power-cut behavior remain
outside local development qualification.

## Application import

Goetic can load a private record-store generation from a stable snapshot of
its current data. Import each present body byte for byte and verify a complete
inventory and readback before closing the owner. Keep absent source records
absent and create stored empty bodies explicitly. The application's revision
history remains inside the exact bytes. Use the new returned record versions
for future CAS.

Goetic owns its generation selector. It can publish the staged generation as
one switch after verification and while application writes are quiesced. Keep
backups outside the engine's recovery path. Inspect the canonical selector if
publication has an uncertain outcome. The Enigma record API does not publish
that selector or provide a transaction across keys.

Qualify the combined NIL SDK and Goetic adapter with synthetic imports before
switching application storage. The earlier Goetic SDK at source `332b6f5`
lacks the runtime lock ownership API. The Enigma development SDK described in
the [development guide](../development.md) covers the record engine's local
tests. Use one matching generation for the application and all imported books.
