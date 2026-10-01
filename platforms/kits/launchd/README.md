# kit launchd

`ai-kit.refresh.plist` runs `platforms/tools/refresh.sh` at login and every six hours. `bootstrap.sh` replaces `@KIT@` with the clone path and installs the rendered file in `~/Library/LaunchAgents/`.

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
