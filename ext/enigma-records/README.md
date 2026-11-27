# Enigma records for Matrix applications

`enigma.records.client` reads, conditionally replaces, and enumerates durable
application records. A record holds exact UTF-8 bytes, including empty bodies
and embedded NUL, independently of any application serialization format.

Add Enigma's `src` and `ext/enigma-records/src` to the application's
`includePaths`. Use a matching complete Linux development SDK with the durable
I/O and lock ownership bindings. See the [development guide](../../docs/development.md).

## Try a synthetic record

From the Enigma repository with `NIL_SDK` selected, build the example and run
it in two processes. The second process reopens the store, explicitly admits a
fresh session, and verifies the persisted bytes and version.

```sh
"$NIL_SDK/nilbuild" build --project ext/enigma-records/nil.project.nildata \
  --sdk "$NIL_SDK" --target native
record_demo="$(mktemp -d "${TMPDIR:-/tmp}/enigma-record-demo.XXXXXX")"
NIL_STRICT_BOUNDS=1 ./ext/enigma-records/build/enigma-records-example create "$record_demo/store"
NIL_STRICT_BOUNDS=1 ./ext/enigma-records/build/enigma-records-example reopen "$record_demo/store"
./scripts/test-records.sh
```

For a VM-only build, use `--target vm` and run the resulting
`enigma-records-example.nil` through `"$NIL_SDK/nilinterpreter"`.
The [Matrix example](examples/main.matrix) shows the full sequence.

## Connect and use a record owner

Import `create_record_database` and `open_record_database` from
`enigma.records.session`. Use `owner.describe_limits()` for storage ceilings
and `owner.describe_state()` for the incarnation and recovered clock floor.
The trusted host admits a session and provisions an explicit grant through
`provision_record_host`. Use `connect_records(owner, grant_id)` and pass a
fresh trusted `access_context` on every client call.

- `get(caller, key, max_body_bytes)` returns exact bytes and the current
  version. `found = false` and version zero mean absence. An empty stored
  body has `found = true` and a positive version.
- `put(caller, key, content, expected_version)` uses version zero for
  create-only and the last observed version for replacement. Save the
  returned version on success.
- `put_checked(caller, key, content, expected_version, guards)` also checks up
  to 16 input versions in the same commit. It uses the caller's read and write
  rights and scan budget. [Guarded write contract](../../docs/design/ENI-0011-guarded-record-writes.md)
- `list_keys(caller, max_keys, max_metadata_bytes, max_scan_keys)` returns the
  full ordered batch with versions and lengths or an empty `limit` receipt.
- `delegate` and `revoke` apply the current grant's authority. Provisioning
  and the caller's logical clock remain with the trusted host.

Check `confirmed` before using a receipt. A confirmed domain refusal
such as `conflict` or `capacity` leaves the proposed data change absent.
An unconfirmed failure with `outcome_unknown` means the operation may have
committed. Close and reopen, re-admit the caller, then inspect state before
attempting another write.

Use one synchronous owner for the life of the NIL invocation and close it
explicitly. Opening scans every referenced body within `max_verify_bytes`
and retires earlier grants before returning a ready owner. Files remain private
and plaintext. Obsolete bodies still use disk space.
[Record contract](../../docs/design/ENI-0009-application-records.md) · [Goetic validation](../../docs/validation.md#goetic-record-consumer--2026-11-21)
