# Enigma work handoffs

Save a handoff or a prior attempt, then check whether the inputs it relied on
have changed. Use this package above the regular Enigma record client.

Add Enigma's `src`, `ext/enigma-records/src`, and `ext/enigma-work/src` to
the Matrix project's include paths. Import types from `enigma.work.model`
and operations from `enigma.work.client`. The package uses the same matching
development SDK as the record client.

| Call | Purpose |
| --- | --- |
| `capture_work_inputs(client, caller, keys, max_keys, max_metadata_bytes, max_scan_keys)` | Capture up to 16 named record versions using one authorized complete listing. |
| `save_work_entry(client, caller, key, entry, expected_version)` | Save a handoff or attempt with record compare-and-set. |
| `load_work_entry(client, caller, key)` | Read a typed entry and its current storage version. |
| `check_work_inputs(client, caller, inputs, max_keys, max_metadata_bytes, max_scan_keys)` | Report `changed` or `unchanged` and the versions that changed. |

Import `resume_work` and `describe_resume_work` from `enigma.work.views`
to expose one named view. The descriptor reports version 1, the `get` and
`list_keys` operations, and the hard resource ceilings.

```matrix
value report is resume_work with client being client, caller being caller,
    handoff_key being "work/42/handoff", max_keys being 128,
    max_metadata_bytes being 16384, max_scan_keys being 128
```

A confirmed `ok` report includes the handoff, its storage version, and
`freshness` with the changed inputs and observed generation. A refusal
clears the entry, version, and comparison data. The view uses both read
and list authority. Its reads can commit a security clock advance.

Import `save_current_handoff` and `describe_save_current_handoff` from
`enigma.work.commands` for a guarded write. The descriptor exposes version 1,
the `put_checked` operation, the 32 KiB body ceiling, up to 16 input conditions,
and one possible record write.

```matrix
value saved is save_current_handoff with client being client, caller being caller,
    key being "work/42/handoff", entry being revised_handoff,
    expected_version being report.version
```

Supply a handoff with the versions it actually relied on. The command checks
the current input versions and saves the handoff in a single owner operation.
Use version zero for a create-only destination or an input observed absent.
A confirmed `dependency_conflict` means an input no longer matches. A confirmed
`conflict` means the handoff's own storage version no longer matches. Both
refusals preserve the existing handoff. The caller needs current read and
write authority and a grant whose scan budget covers the named inputs. This
command uses exact input keys without a listing. Inspect an uncertain outcome
before trying the write again.

A handoff can hold a short summary and the next step. An attempt also needs
an outcome, such as “blocked on a missing linker.” Capture the SDK configuration
record as an input. If the SDK record changes, a later check flags the attempt
for review. Save later attempts at new keys to keep the investigation history.

Every call takes the current trusted application context. Capture and check
use list permission and the explicit listing budgets. Loading requests up to
32 KiB of current read authority. Saving uses the normal write authority and
the entry's encoded size. Check `confirmed` and then `code` before using a
reply. A budget refusal provides no comparison. An unconfirmed write with an
unknown outcome requires inspection before another attempt to save.

The package compares versions of named records in one database. Freshness from
a view describes its observed generation. Use the guarded command to check the
same preconditions at the write. See the [handoff contract](../../docs/design/ENI-0010-work-handoffs.md).

The [create and resume example](../../validation/work/main.matrix) shows
the full sequence with a synthetic task. Run it through the test runner
with the selected Enigma SDK.

```sh
./scripts/test-work.sh
```
