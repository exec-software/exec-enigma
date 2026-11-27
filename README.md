# Enigma

Enigma is an experimental database engine for humans and AI agents, written
in **Matrix** on the [NIL Framework](https://github.com/exec-software/exec-nil-framework).
Its intended query language takes Matrix's readable, explicit syntax as its
starting point. Data security is a core design requirement.

The engine and executable are **Enigma** and `enigma`.

## Current state

**0.1.0-dev includes a durable evidence engine and a separate application record
store.** An evidence proposition is
`(subject, relation, object_value)`. Supporting and opposing reports coexist,
with source attribution and the acting entity/session. Withdrawing evidence
appends an event; earlier snapshots keep their original meaning.

- Resolve a proposition as `unknown`, `supported`, `contradicted`, or `contested`.
  These describe evidence, not objective truth or probability.
- Receive evidence IDs, counts, revision, and separate scan/output completeness.
  A budget-exhausted scan reports `incomplete`.
- Discover active reports using exact-or-any proposition fields, including their
  source and acting entity/session, without guessing complete triples.
- Use scoped, session-bound grants with operation, expiry, and work/output
  limits; delegation can only narrow authority and ancestor revocation stays live.
- Reclaim withdrawn evidence under a separate scope-wide compaction permission;
  reads of history below the retention horizon report `incomplete`.
- Interact through a typed Matrix companion library in
  [`ext/enigma-client`](ext/enigma-client/README.md), outside `nil.std`.
- Embed a durable owner and typed application client through
  [`ext/enigma-durable`](ext/enigma-durable/README.md), with explicit close and
  distinct confirmed receipts and uncertain failures.
- Preserve retained evidence, grant ancestry and revocations, issued counters,
  and the logical clock floor in one validated checkpoint. Recovery retires all
  prior session grants, reclaims their rows, and retains the retirement mark
  before serving requests.

The [evidence contract](docs/design/ENI-0001-evidence-and-authority.md) defines
evidence semantics. The [persistence contract](docs/design/ENI-0002-durable-state-and-recovery.md)
defines commit and recovery behavior.

The application record store preserves exact UTF-8 bodies up to 4 MiB. It
supports conditional replacement by version and complete ordered enumeration,
with explicit byte and key budgets. Goetic uses the typed Matrix package for
durable workspace storage on a qualified Linux development SDK.
[Record package](ext/enigma-records/README.md) · [Consumer validation](docs/validation.md#goetic-record-consumer--2026-11-21)

The work companion records handoffs and prior attempts. Agents and people can
check whether the record versions behind an entry have changed before picking
up the task. [Work package](ext/enigma-work/README.md)

Authority follows Anomalous's model, currently implemented as a trusted-host
policy fixture. Matrix fields are public: this is **not isolation against hostile
code in the same process**. Context identity and fresh logical ticks come from
the embedding host. There is no authentication, network listener, query parser,
encryption, or native Anomalous integration. The direct embedded client remains
volatile. Durable evidence acknowledgements come through a persistence host or
`enigma.durable`. Application records use the importable `enigma.records` owner.

## Build and run

Choose a durable evidence or record package in the
[application guide](docs/applications.md).

Install or build a complete NIL SDK using the
[development guide](docs/development.md). Discovery's optional text fields need
the compiler fix pinned there; an older SDK with the same version string may
lack it. From this checkout:

```sh
export NIL_SDK=/absolute/path/to/exec-nil-framework/sdk
./scripts/nil.sh check
./scripts/nil.sh build --target all
./scripts/nil.sh run -- --help
./scripts/nil.sh run -- --version
./scripts/nil.sh run -- --surface
./scripts/nil.sh run -- --demo
./scripts/test.sh
```

`build --target all` builds VM and native outputs. Native compilation needs an
LLVM-enabled SDK and a host C++ linker. Use `--target vm` for VM-only development,
including `./scripts/test.sh --target vm`.

If this project sits beside `exec-nil-framework`, its `sdk/` is discovered
automatically. The wrapper always enables runtime bounds checks. Directly
running generated binaries requires `NIL_STRICT_BOUNDS=1` as well.

The synthetic demo exercises competing evidence, history, bounded work, and live
revocation:

```text
Enigma evidence demo (synthetic, in memory)
initial: supported
after opposition: contested
after withdrawal: supported
historical revision 2: contested
budget 1: incomplete
after revocation: denied
```

`--surface` emits a NILData description of the companion operations and hard
limits. The client accepts typed requests; it does not need to generate query
strings. Stores currently hold at most 1,024 retained events, with assertions
limited to 1,023 to reserve a withdrawal slot. Read work can cover 1,024 events;
returned evidence stays capped at 128 items. Retracted evidence is reclaimable
on request. All data disappears at process exit in this embedded demo. Durable
stores also enforce separate encoded evidence and grant budgets; see
[ENI-0008](docs/design/ENI-0008-bounded-capacity.md).

## Evidence persistence and recovery

Build the Matrix evidence worker, then create a new synthetic evidence store:

```sh
./scripts/build-storage.sh --target all
mkdir -p data
python3 scripts/store.py init data/example --scope work
python3 scripts/store.py serve data/example
```

The Python 3 host is POSIX-only. It holds an exclusive writer lock and publishes
a receipt only after syncing a private candidate checkpoint, atomically replacing
the canonical checkpoint, and syncing the database directory. Initialization
also syncs the parent directory. Matrix owns the codec, state validation, and
recovery decisions; the host supplies missing filesystem primitives.

`serve` commits a fresh incarnation and retires **all** prior session grants
before returning `ready`. Retired grant rows are reclaimed; issued counters and
a retirement high-water mark remain. Callers require explicit re-admission and
newly installed grants. Saved
old-incarnation requests cannot restore authority. Missing or corrupt state
fails closed; there is no automatic initialization or older-checkpoint fallback.

See [the persistence guide](docs/persistence.md) for request examples and failure
semantics. Guarantees assume trusted storage ancestry and a local filesystem
honoring synchronization, rename, and locks. SHA-256 detects corruption; it is
not encryption, authentication, or general rollback protection. Hardware
power-cut behavior has not been qualified.

## Project map

| Path | Purpose |
| --- | --- |
| `nil.project.nildata` | NIL project settings; analyzer warnings fail checking. |
| `src/main.matrix` | Executable entrypoint. |
| `src/enigma/ledger.matrix` | Append-only evidence, temporal reads, bounded resolution. |
| `src/enigma/discovery.matrix` | Bounded pattern discovery of active evidence with provenance. |
| `src/enigma/evidence_batch.matrix` | Bounded typed batches of returned evidence. |
| `src/enigma/authority.matrix` | Host grant lifecycle and authorization. |
| `src/enigma/persistence.matrix` | Checkpoint codec and semantic recovery validation. |
| `src/enigma/storage.matrix` | Staged durable operation and recovery transitions. |
| `src/enigma/records/` | Durable application record index, authority, and owner. |
| `storage/` | Separate Matrix storage-worker project. |
| `scripts/store.py` | POSIX locking, integrity envelope, sync barriers, and receipts. |
| `ext/enigma-client/` | Companion Matrix library, tests, and standalone example. |
| `ext/enigma-durable/` | Durable evidence session, typed client, and persistent example. |
| `ext/enigma-records/` | Application record client and create/reopen example. |
| `scripts/` | SDK selection, strict-bounds execution, and validation. |
| [Design](docs/design/README.md) | Architecture, query direction, and first milestones. |
| [Security](SECURITY.md) | Current limits, reporting, and intended threat boundaries. |
| [Contributing](CONTRIBUTING.md) | Development expectations. |

## License

MIT. See [LICENSE](LICENSE).
