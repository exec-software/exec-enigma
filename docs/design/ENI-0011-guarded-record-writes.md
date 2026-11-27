# ENI-0011: Guarded record writes

A handoff can describe the result of reading a test report, a workspace
configuration, and an open issue. The record version of the handoff protects
that document from an overwrite. A guarded put also checks the versions of
the records behind the proposed change while the owner is committing it.

## Typed operation

`record_client.put_checked(caller, key, content, expected_version, guards)`
returns the existing `record_reply<record_put_receipt>`. The destination uses
the ordinary version precondition. Version zero requires that the destination
does not exist.

The `record_conditions` type in `enigma.records.conditions` carries a
`database_id` and parallel arrays named `keys` and `versions`. The database
checks one to sixteen distinct input keys. The destination has its own
precondition, so it cannot also appear in the input keys. Each expected
input version must be exact. An expected version of zero requires absence.

Use the versions observed when reading the inputs. A change to a key outside
the supplied conditions leaves the write eligible. The condition set is
a declaration by the caller, so callers choose which observations to include.
A condition checks manifest metadata. Use a normal read to verify the body
and its digest.

## Authority and resource bounds

A guarded write requires current read and write rights on the same store.
The engine checks both before interpreting the conditions or examining input
metadata. The count of condition keys must fit the grant's
`max_scan_keys`. Each condition is an exact index lookup. The write consumes
the ordinary body byte budget. The guard reads version metadata only, so it
needs no list right or body read budget.

Ownership checks and a fresh trusted caller context apply on every call.
The database ID binds the conditions to one store across reopen. Reopen
still retires prior grants. A fresh caller can supply conditions from the
same database if their exact versions still match.

## Commit and receipt

The owner checks the input versions and stages the destination update from
the same manifest under its writer lock. It uses the existing body and
manifest publication sequence. The engine returns success after durable
publication. A confirmed domain refusal advances neither the record sequence
nor the body inventory. It can commit a newer authority clock floor, like an ordinary
record refusal.

| Result | Meaning |
| --- | --- |
| `ok` | Every declared input matched and the destination committed. |
| `dependency_conflict` | At least one input version or absence expectation failed. |
| `conflict` | The destination version precondition failed. |
| `foreign` | The condition set belongs to another database. |
| `invalid`, `limit`, `denied` | The request, budget, or current authority did not allow the operation. |

Refusals clear the receipt version and length. A dependency conflict contains
no current version or failing key. The caller can read inputs independently
under current authority. Publication failures preserve the existing
uncertainty flag and poison the owner. Reopen and inspect state before
retrying an uncertain write.

This operation publishes one body in one record database. It guards a write
against the specified input versions, with the same trusted storage and
rollback limits as ordinary puts. Evidence checks across another store,
multi-record commands, and external effects have separate commit contracts.

## Named command

`enigma.work.commands::save_current_handoff` uses `put_checked` directly with
the versions stored in the submitted handoff. It saves a new handoff with a
destination version of zero or replaces one at its expected version. Its
descriptor exposes its one record write and resource ceiling. The command
keeps the captured generation for the later resume view. Its commit
conditions are the database identity and exact input versions.

See the [work package example](../../ext/enigma-work/README.md) and run
`./scripts/test-guarded.sh` for the VM and native fixtures.
