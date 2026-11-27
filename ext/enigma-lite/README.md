# Enigma Lite

Embed Enigma in a local Matrix application for settings and small pieces of
state. Lite uses the regular durable record format inside the application
process. It needs the Enigma development SDK for builds and no database
server or worker process at runtime.

Add Enigma's `src`, `ext/enigma-records/src`, and `ext/enigma-lite/src` to
your application's include paths. Import `create_lite` and `open_lite`
from `enigma.lite`.

```matrix
value opened is open_lite with directory being settings_path
when opened.code equals "ready" then
    value current is opened.store.get with key being "theme"
    when current.confirmed and current.code equals "ok" then
        value saved is opened.store.put with key being "theme",
            content being "dark", expected_version being current.version
        say saved.code
    end when
    evaluate opened.store.close with nothing
end when
```

Use `create_lite(directory)` once to create a private store. It reports
`created`. `open_lite(directory)` opens a valid existing Lite directory and
reports `ready`. Close the store explicitly before opening another owner
for the same directory.

`get` returns `found = false`, empty content, and version zero for a missing
key. A stored empty string has `found = true` and a positive version.
`put` expects version zero for a create-only write or the current version
for replacement. Check `confirmed` and `code`. If `outcome_unknown` is true,
close and reopen to inspect the result before retrying.

| Resource | Lite ceiling |
| --- | --- |
| Keys | 16 |
| One text value | 64 KiB |
| Live text values in total | 256 KiB |

Values are UTF-8 text without NUL. `describe_lite()` returns the limits.
The trusted application owns the local session. Lite sets up a short scoped
read and write grant for that owner and opens a fresh session after restart.

A compatible Lite directory can be opened with the full record client when
an application needs larger limits or explicit grant management. Full record
writes can exceed Lite's limits. Lite checks the scope and limits before
recovering a store. Replaced bodies can still occupy disk outside the live
byte limit. See the [Lite contract](../../docs/design/ENI-0012-lite-records.md).

Run the [create and reopen example](examples/main.matrix) and filesystem
checks with the selected SDK.

```sh
./scripts/test-lite.sh
```
