# ENI-0012: Lite record stores

Lite serves local applications that need durable settings and small state.
It uses the record engine and the `enigma.records.v1` manifest and body
format. The companion `enigma.lite` exposes create, open, get, put, and
close inside a Matrix application. It runs in the application process.
The underlying record engine and matching NIL SDK still apply.

## Store profile

Lite uses the fixed scope `enigma.lite.v1`. Its owner admits up to 16 keys,
64 KiB per body, and 256 KiB of total referenced body bytes. Text values
can be empty and must be UTF-8 without NUL. The full record profile
supports UTF-8 bodies containing NUL, so Lite reports `invalid_text` when
asked to read such a body.

The record engine sets its bounds for the active owner. A bounded open
holds the usual exclusive lock while inspecting the manifest. A different
scope returns `scope_mismatch`. Exceeding a key, body, or live byte limit
returns `limit`. Both checks precede body verification and any durable
recovery transition, so refusal leaves the canonical manifest intact.

Lite writes check limits before publishing a new body. Replacing a value
accounts for the difference between its new and old lengths. Count and
byte refusals preserve the prior records and their versions. Replaced
and unreferenced files still use disk space. The byte ceiling counts live
data.

The same directory and format are usable through the full record API.
A host choosing to open with full limits can grow the store beyond Lite's
bounds. Lite will refuse to open an incompatible store. The profile
does not require a storage conversion.

## Embedded authority

Create and open are trusted host operations. Lite provisions one local
read and write grant scoped to that owner. The grant is bound to its current
incarnation and logical session. Lite supplies a fresh context at the same
admitted tick for each call, so routine settings reads do not commit an
authority clock update. Recovery retires prior grants and provisions a new
session at a tick above the durable clock floor. Application code keeps one
owner in one synchronous NIL invocation and closes it explicitly.

Lite keeps the record engine's private directory and file checks, runtime
lock checks, compare-and-set writes, and durable publication ordering. An
ordinary refusal carries a confirmed result. An uncertain publication
failure disables the owner and requires recovery and inspection. Lite
uses the same trusted-process and plaintext boundary as full records.

See the [companion package](../../ext/enigma-lite/README.md) for an example
and [ENI-0009](ENI-0009-application-records.md) for the format and recovery
contract.
