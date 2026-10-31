# kit launchd

`ai-kit.refresh.plist` runs `platforms/tools/refresh.sh` at login and every six hours. `bootstrap.sh` replaces `@KIT@` with the clone path and `@HOME@` with the home directory (launchd does not expand `~`), then installs the rendered file in `~/Library/LaunchAgents/`.

The job's `PATH` is `~/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin`, so a `claude` in `~/.local/bin` wins over Homebrew's, as in a login shell that lists `~/.local/bin` first. When `refresh.sh` finds no `claude` or `codex` CLI it logs a `skip:` line; the `claude` line prints the `PATH` it searched. A plist installed before 11.3.0 keeps the old `PATH` until `bootstrap.sh` runs again.

Inspect:

```bash
launchctl print gui/$UID/ai-kit.refresh
tail /tmp/ai-kit.refresh.log
```

Remove:

```bash
launchctl bootout gui/$UID/ai-kit.refresh
rm ~/Library/LaunchAgents/ai-kit.refresh.plist
```
