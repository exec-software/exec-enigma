# ENI-0010: Work handoffs and attempt history

A handoff records what the next person or agent needs to know about a task.
An attempt records what somebody tried, the observed outcome, and what to
try next. Both carry versions of the records that informed the entry. A
successor can read the entry, check those versions, and decide which work
to resume or repeat.

This experiment lives in the Matrix companion package under
`ext/enigma-work`. Its entries are ordinary Enigma records. The application
picks the keys and the granularity of each input. For example, it can keep the
latest handoff at `work/42/handoff` and individual attempts at
`work/42/attempt/native-1` and `work/42/attempt/native-2`. Use create-only puts
for new attempts and the saved handoff's current version when updating that
handoff. Keeping the attempts under distinct keys preserves their history.

## Record format and bounds

An entry has a `kind` of `handoff` or `attempt`, a task identifier, a short
summary, an outcome, a next step, and a set of input versions. An attempt
requires an outcome. These fields hold observations and guidance supplied by
the application.

Inputs are exact record keys with versions taken from one complete listing.
A version of zero records an absent key. The capture includes the database
identity and manifest generation, so reopening the same database preserves
its identity and a different database cannot accidentally match its version
numbers. Capture accepts one to sixteen distinct keys. Encoded entries are
bounded at 32 KiB, with smaller UTF-8 byte limits per field.

Use the versions you actually worked with. If you capture the inputs before
reading the bodies, compare each subsequent read's returned version with the
capture. A capture records which versions existed at that point. It cannot
attest which bodies an author read or how an author reached a conclusion.

## Checking an entry

The check obtains one complete current inventory through `list_keys` under
the caller's existing authority and explicit enumeration limits. It verifies
that the capture and inventory belong to the same database and compares just
the named versions. An unrelated write, new session, or unchanged record body
at its original version leaves a captured input unchanged. Replacing a
captured key, including writing the same bytes again, changes its version.
Creating a previously absent key also changes the result.

| Result | Meaning |
| --- | --- |
| `unchanged` | All named versions match at the returned generation. |
| `changed` | The reply contains the changed keys and their observed versions. |
| `foreign` | The authorized inventory belongs to another database. |
| `limit`, `denied`, `incomplete` | A complete comparison was unavailable. |
| Unconfirmed | The storage or session call failed. Inspect its code and uncertainty flag. |

Refusals contain no observed keys, versions, or generation. Each successful
comparison is a point-in-time metadata observation. Loading a body still
runs the record API's integrity checks. A later write requires its own
version preconditions. The check cannot detect a coherent operator rollback
that restores and reuses the same versions.

## Resume view

`resume_work` loads the handoff through the ordinary record client, observes
the owner's generation, and checks the handoff's input versions.
It returns the entry and comparison only when both reads succeeded and the
comparison used that same generation. These operations run synchronously on
one owner. The first read can advance the security clock before the view
records the generation.

The view takes an explicit handoff key and listing bounds. Attempt records
continue to use the separate load and check operations. If a read, authority
check, listing budget, or generation check fails, the view returns a blank
entry and comparison and preserves the operation's status and uncertainty.
The view performs no application-record writes. Authority checks can still
persist a security clock advance.

## Authority and storage

Apps use the same trusted host and ordinary record API. Current list authority
is required for capture and check, current read authority for load, and
current write authority for save. The entry stores no session grant or
credential. After reopening, establish fresh admission before using it.
A stored reference may name a different database. Checks refuse it even if
another database has the same numeric versions.

The package uses ordinary compare-and-set on the entry itself. It preserves
confirmed conflicts and unconfirmed storage replies and leaves the decision
to retry with the caller. The first slice observes application record versions
within one database. The named command `save_current_handoff` applies these
record versions as commit conditions. Evidence queries remain a separate
capability. [Guarded write contract](ENI-0011-guarded-record-writes.md) Entry summaries are application data in the
scope where they are saved, so the application is responsible for choosing
what to copy into a note.

Run `./scripts/test-work.sh` for VM and native checks with a synthetic store.
See the [companion package guide](../../ext/enigma-work/README.md).
