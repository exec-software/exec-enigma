# Development validation

## Guarded record writes — 2026-11-26

`./scripts/test-guarded.sh` passes six Matrix executions and two independent
process scenarios on VM and native. The suite passes on both the Enigma
development SDK from `dbb4379` and Goetic's combined Linux development SDK
from `167ae3a` (manifest
`5931094a3cf696f0c176d370864df4b15c4f22f108074f9ca682a3db15f8388a`).

The guarded command commits after reopen with fresh authority and matching
input versions. An unrelated write leaves those conditions matched. A changed
input or a newly present key rejects the write with an empty conflict receipt.
The filesystem oracle verifies that confirmed refusals leave both the record
sequence and the body inventory intact. It also verifies normal authority
clock commits and an uncertain manifest publication after matching conditions.
The failed publication poisons the owner and leaves its unused staged body
outside the canonical manifest.

On the Enigma SDK, `./scripts/test-records.sh`, `./scripts/test-work.sh`, and
`./scripts/test.sh` also pass. These runs exercise ordinary record puts,
maximum-size record round trips, handoff resume, and the evidence suites.
The combined SDK run exercises the guarded fixture. Goetic's existing
application deployment uses its separately pinned engine source.

## Named resume view — 2026-11-26

`./scripts/test-work.sh` passes on VM and native with the same development SDK
used for the work companion. The restart fixture calls the named view and
checks its descriptor, the unchanged result, and both changed inputs from
one observed generation. A caller with read authority can load the handoff
directly. Without list authority, the view refuses and clears the handoff and
comparison. An insufficient scan budget also clears the report.

The view can persist the caller's newer clock floor. The external filesystem
check verifies the new floor while the application record sequence and saved
handoff bytes stay fixed. `./scripts/test.sh` passes the ordinary evidence and
host regression suite.

## Work handoffs and attempt history — 2026-11-26

The companion source is
[`5e00298`](https://github.com/exec-software/exec-enigma/commit/5e002987188c8fcd09b269b9657a3aa9bbb4d035).
Validation used the Linux x86_64 development SDK from NIL source `dbb4379`,
generation `936298a9c20142f2634744a0154ee32d7e5807cc1f3f743d08059fab61f0b7bf`.

`./scripts/test-work.sh` passes six Matrix codec executions and a separate
process persistence scenario on both VM and native. The scenario stores a
handoff and a failed build attempt, reopens the record store, and verifies
fresh authority. An unrelated write leaves the input versions unchanged.
Replacing the SDK record and creating a previously absent test report flags
both entries for review. The filesystem oracle verifies the saved entry
bytes and versions independently. Budget, denied, and foreign comparisons
reveal no observed metadata. A duplicate create-only write is refused.

`./scripts/test.sh` also passes 176 Matrix executions, 24 CLI checks, both
volatile examples, and 40 Python methods. The work probe runs under its
separate runner. Goetic's pinned record source trees match this revision.
See the [handoff contract](design/ENI-0010-work-handoffs.md).

## Goetic record consumer — 2026-11-21

Goetic's workspace migration uses Enigma source
[`2eec2bd`](https://github.com/exec-software/exec-enigma/commit/2eec2bd7d9188367f3548294e6f2510f98501569),
which contains the same engine source as `942c47a`. The consumer pins combined
Linux development SDK manifest
`5931094a3cf696f0c176d370864df4b15c4f22f108074f9ca682a3db15f8388a`
from NIL source `167ae3a6b0abb69c26e943a008ee6eb1eac8f13d`.

Goetic reports 26 Matrix tests, 101 HTTP checks, and 23 migration filesystem
checks passing in isolated validation. Its real adapter and transfer tests
cover staged import, exact body preservation, activation, subsequent writes,
restart, and refusal of corrupt or foreign selected storage. Goetic reports
the live cutover completed with its original records preserved.
[Goetic integration validation](https://github.com/exec-software/exec-goetic/blob/9d99e801012e24582b1ac14e7bae0949b91799e6/code/exec-goetic/docs/enigma-validation.md)

Goetic uses the interpreter for its long-lived owner and client bindings.
The Enigma VM and native tests below qualify the standalone record API on
Enigma's development SDK.

## Application record storage — 2026-11-21

The source revision is
[`942c47a`](https://github.com/exec-software/exec-enigma/commit/942c47acace097d4c4b285c2b0ed8afe2210b1ef).
The complete Linux x86_64 development SDK is built from clean NIL source
[`dbb4379`](https://github.com/exec-software/exec-nil-framework/commit/dbb4379946f6800a79e485dcd890e8f5b0902b31),
generation `936298a9c20142f2634744a0154ee32d7e5807cc1f3f743d08059fab61f0b7bf`.

```sh
./scripts/test-records.sh
./scripts/test.sh
./scripts/test-durable-client.sh
./scripts/test-matrix-host.sh
```

- The record runner passes 22 Matrix executions and five external filesystem
  methods on both VM and native. The synthetic package example also passes
  separate-process create and reopen on both routes.
- The evidence runner passes 176 Matrix executions, 24 CLI checks, the two
  volatile examples, and 40 existing Python methods.
- The durable evidence client runner passes 46 Matrix executions and nine
  external methods on both routes. The session and fault contracts pass
  against Matrix VM, Matrix native, and Python hosts, including both
  checkpoint interoperability directions.

The record oracle checks exact 4 MiB UTF-8 bodies with embedded NUL and
independently compares persisted and exported bytes and SHA-256 digests.
A seeded 1,025-key manifest recovers, refuses a short scan without a prefix,
enumerates all keys in order, and durably accepts key 1,026. The index suite
also checks the 2,048-key ceiling and the independent encoded byte ceiling.
Tests cover missing versus empty, version preconditions, byte grant
attenuation, durable clock advancement, recovery retirement, and no version
advance on refusal.

External filesystem failures distinguish a known absence of logical
publication from an uncertain manifest outcome. An affected owner refuses
further dispatch. Missing, unsafe, or corrupt referenced files and malformed
manifests block opening. An active read detects modified body bytes and
poisons its owner. These cases exercise real processes and files on Linux.

The tests qualify the record profile on the pinned Enigma development SDK.
The format stores plaintext bodies and retains unreferenced
files after replacement or interrupted writes. See
[ENI-0009](design/ENI-0009-application-records.md).

## Bounded checkpoint capacity — 2026-11-21

Engine source is
[`9408f12`](https://github.com/exec-software/exec-enigma/commit/9408f128e7793ee8c9aa44fcf3899a1a0059fede).
Validation used the same complete Linux x86_64 development SDK from clean NIL
source [`dbb4379`](https://github.com/exec-software/exec-nil-framework/commit/dbb4379946f6800a79e485dcd890e8f5b0902b31),
immutable generation `936298a9c20142f2634744a0154ee32d7e5807cc1f3f743d08059fab61f0b7bf`.
The SDK and framework source were unchanged by this capacity work.

```sh
./scripts/test.sh
./scripts/test-durable-client.sh
./scripts/test-matrix-host.sh
./scripts/test-capacity.sh
```

- The full runner passes 176 Matrix executions across VM/native, 24 CLI checks,
  both volatile examples, and 40 existing Python methods. Twenty methods are
  deliberately skipped there: nine application, five capacity, and six
  host-fault methods belong to the separate runners.
- The application runner passes 46 Matrix executions and nine external Python
  methods, each exercised on VM/native.
- The host runner passes the shared host logic, all 13 recovery and six external
  fault methods against Matrix VM, Matrix native, and Python hosts, and both
  checkpoint interoperability directions.
- The capacity runner passes 16 enabled method/profile executions: five against
  each Matrix route and three against each Python-worker route. Four typed
  cases are intentionally skipped on the Python profiles because the same
  typed fixture already ran on each route.

The expanded-store oracle independently seeds 1,023 assertions, verifies full
counts with 128-item replies, proves small grants stay small, appends the reserved
withdrawal at revision 1,024, and explicitly compacts its pair. Recomputed-digest
fixtures with too many rows, a missing event beyond the former ceiling, or a
duplicate withdrawal fail closed without rewriting the canonical file.

The byte-capacity oracle uses control characters and UTF-8. A refused write
preserves evidence, grant definitions, issued identifiers, and revision while
committing its observed clock floor and successor generation. The same owner
continues serving; revocation, restart retirement, and fresh admission remain
usable. Typed capacity replies are confirmed domain refusals rather than
uncertain failures. Existing full-width legacy checkpoints still admit fresh
read grants and return complete batches through both hosts and the typed client.

A separate 1,024-event history with 512 assertions and 512 withdrawals passes
codec round trips, complete empty resolution, full compaction, and next-ID
checks on both routes. Its entire fixture took 8.63 seconds on VM and 15.40
seconds native; these are test timings, not isolated-operation benchmarks.
All external receipt/phase timeouts remain 30 seconds. Shell/Python syntax,
local documentation links, and `git diff --check` pass.

This qualifies the bounded checkpoint profile in
[ENI-0008](design/ENI-0008-bounded-capacity.md), not document storage, scalable
query latency, release SDKs, encryption, native admission, general rollback
protection, or hardware power-cut behavior. The application record profile in
[ENI-0009](design/ENI-0009-application-records.md) was proposed at that point.

## Durable application integration — 2026-11-20

Application source is
[`d2fe038`](https://github.com/exec-software/exec-enigma/commit/d2fe0389c5ab4b1f1eba7144ffe982d9338a4b0c).
The matching complete development SDK is built from clean NIL source
[`dbb4379`](https://github.com/exec-software/exec-nil-framework/commit/dbb4379946f6800a79e485dcd890e8f5b0902b31),
including `file_lock_is_held` in
[NIL PR #42](https://github.com/exec-software/exec-nil-framework/pull/42).
Its manifest reports `worktree_dirty: false`, and the workspace's ignored `.sdk`
link selects that immutable generation.

These commands pass on Linux x86_64:

```sh
./scripts/test-durable-client.sh
./scripts/test-matrix-host.sh
./scripts/test.sh
```

- The application runner passes 44 Matrix executions across VM/native: five
  typed codec/reply tests and 17 shared session/host tests per route.
- Nine independent Python application tests pass on both routes. They exercise
  all nine typed operations, separate-process create/reopen, old-grant refusal,
  fresh admission, revocation, contention, explicit close, failed-open cleanup,
  stale-owner refusal, poisoned-session refusal after external storage failure,
  working-directory pinning, literal POSIX backslashes/UTF-8, and a full-width
  128-report typed discovery batch. Lock release is checked while the application
  process is still alive.
- The refactored CLI passes the existing 13 recovery and six storage-fault tests
  against Matrix VM, Matrix native, and Python hosts. Both checkpoint
  interoperability directions pass. The same 17 shared Matrix tests also run
  through that host project.
- Core regressions pass 170 Matrix executions, 24 CLI checks, both volatile
  package examples, and the existing Python persistence tests. Application and
  host-fault cases deferred by that default runner execute in the dedicated
  runners above.
- Seven focused NIL helper, embedded-VM lifecycle, Ny/Matrix route, native ABI,
  and ordinary-I/O groups pass. They include current/stale/foreign lock queries,
  invocation teardown, and forged return-schema rejection.

The SDK was packaged in development mode with `NIL_RUN_TESTS=OFF`; focused NIL
checks ran separately. Its runtime source remains pinned at `dbb4379`; later
branch documentation records the open Matrix imported-choice naming defect
(F93) found during integration. Application code avoids that defect without
relaxing the loader. Direct typed reply records preserve the existing closed
class-provenance profile rather than putting a class-bearing discovery result
inside a general enum carrier.

This validates the bounded POSIX application integration, not full NIL-suite,
release-SDK, production-data, or hardware power-cut qualification. See
[the application guide](applications.md) and
[ENI-0007](design/ENI-0007-application-sessions.md).

## Bounded discovery — 2026-11-20

Engine source is
[`0d2d150`](https://github.com/exec-software/exec-enigma/commit/0d2d15097feda7370aaef6bd18526b1086d8a6f4).
The complete development SDK was packaged from clean NIL source
[`ebc4eb5`](https://github.com/exec-software/exec-nil-framework/commit/ebc4eb518156248cee9dbc6585d16ba09eb464f3),
including the optional-text field fix in
[NIL PR #42](https://github.com/exec-software/exec-nil-framework/pull/42).
The SDK manifest reports `worktree_dirty: false`. The workspace selects that
immutable SDK generation through the ignored project-local `.sdk` link.

With that SDK selected, these commands pass on Linux x86_64:

```sh
./scripts/test.sh
./scripts/test-matrix-host.sh
./scripts/test-nil-io.sh
```

- The full suite passes 170 Matrix executions across VM/native, 24 CLI checks,
  and both package examples. Of 46 Python methods, 40 pass and six host-fault
  methods are deliberately deferred to the host-specific runner.
- The host runner passes 26 Matrix host test executions. The same 13 recovery
  and six storage-fault tests pass against the Matrix VM host, Matrix native
  host, and Python host. Both checkpoint interoperability directions pass.
- The independent NIL I/O consumer passes VM/native, including private modes,
  lock release, checkpoint/envelope bytes, and digest checks.

Discovery tests cover exact/any selectors, literal wildcard characters, current
authority and ancestor revocation, historical withdrawals, retention horizons,
and independent scan/output completeness. The real hosts also return all 128
full-width, escape-heavy reports from a validated synthetic checkpoint.

Staging tests check typed/wire parity, escaped-data injection resistance,
unchanged small-frame bytes, frames above NILData's individual 1 MiB document
limit, and the inclusive 2 MiB worker limit including its newline. One extra
byte returns a fixed failure. Host byte-conversion tests preserve empty input,
chunk boundaries, non-NUL bytes, and UTF-8 split across a chunk. The maximum-size
case passes with the original receipt timeouts after chunked conversion.

Ten focused NIL field/enum/ABI route groups pass, including paired Ny/Matrix
record and class fields with `Option<text>` and `Result<text,text>`. The source
SDK build used `NIL_RUN_TESTS=OFF` in development mode; those route checks ran
separately. This is focused consumer evidence, not full NIL-suite, release-SDK,
cross-platform, or hardware power-cut qualification. Earlier compilers can run
the pattern on the VM but lack the field metadata fix needed by native code.
The [development guide](development.md) pins the required source revision.

## Retention and durable host — 2026-11-20

Validated on Linux x86_64 on 2026-11-20. Engine source is
[`3cea3cb`](https://github.com/exec-software/exec-enigma/commit/3cea3cb48c4ee124bfadb8843e6168c25dc3d77d).
The matching NIL development SDK was packaged from clean source
[`451a4ff`](https://github.com/exec-software/exec-nil-framework/commit/451a4ff2328f2ff7552588e7fc74e23bcf81ce42),
proposed in [NIL PR #42](https://github.com/exec-software/exec-nil-framework/pull/42).
Compiler, native runtime, and standard-library sources came from that same
SDK generation; its manifest reports `worktree_dirty: false`.

### Commands and results

With `NIL_SDK` selecting that development SDK:

```sh
./scripts/test.sh
./scripts/test-nil-io.sh
./scripts/test-matrix-host.sh
```

- The full suite passes 138 Matrix test executions across VM/native, 24 CLI
  checks, and both package examples. Python discovers 43 methods, with 37
  passing and six host-fault methods deliberately skipped until a host command
  is selected by the separate runner below.
- The NIL I/O consumer passes on VM/native. An independent Python oracle checks
  checkpoint bytes and envelopes, SHA-256, private modes, and released locks.
- The Matrix host's own logic passes on VM/native. The same ten recovery tests
  and six external storage-fault tests pass against the Matrix VM host, Matrix
  native host, and Python host. Both checkpoint interoperability directions pass.
- The full suite also passes against the previously installed sibling SDK, so
  the Python persistence path does not require the new NIL additions.

The new regressions require explicit compaction right `16`, preserve the
meaning of existing masks, deny delegated authority after ancestor revocation,
and refuse missing recent checkpoint events even when their envelope digest
has been recomputed. Historical reads below a compaction horizon stay
`incomplete` across restart; old session grants stay denied.

In the NIL source checkout, all 14 selected CTest groups pass: durable helper
faults and lock lifecycle, embedded console state, private directories,
static/shared native ABI, durable routes, existing byte/ordinary-I/O routes,
console routes, and paired secure-hex routes. Directory symlinks ending in `/`
and failed embedded streams with zero `errno` have focused regressions.

### Qualification boundary

SDK packaging used `NIL_RUN_TESTS=OFF` in development mode; the selected CTests
above ran separately. This is focused source-runtime and consumer evidence,
not full NIL-suite, release-SDK, cross-platform, or hardware power-cut
qualification. The installed SDK remains unchanged. `scripts/store.py` remains
the default persistence host while the Matrix host needs the unreleased NIL
surfaces. The limits in [ENI-0002](design/ENI-0002-durable-state-and-recovery.md)
and [ENI-0003](design/ENI-0003-matrix-durable-host.md) still apply.
