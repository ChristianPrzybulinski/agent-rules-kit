#!/usr/bin/env bash
# Scaffold for the eval case: a Spring service with field injection, plus the kit's `java` rule as the synced copy a project carries in
# .claude/rules/, so Claude Code loads it by path when the case reads a matching file (KIT-080, #275). The rule is read
# from this case's plugin folder; a scaffold that cannot reach it stops instead of testing nothing.
set -euo pipefail
rule="$(dirname "${BASH_SOURCE[0]}")/../../rules/java.md"
[[ -f "$rule" ]] || { echo "fixture: kit rule $rule not reachable from the scaffold" >&2; exit 1; }
git init -q -b main .
mkdir -p .claude/rules
cp "$rule" .claude/rules/guardrails-java.md
mkdir -p src/main/java/game
printf '<project><modelVersion>4.0.0</modelVersion><groupId>game</groupId><artifactId>game</artifactId><version>1</version></project>\n' > pom.xml
cat > src/main/java/game/PlayerService.java <<'JAVA'
package game;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class PlayerService {
    @Autowired
    private PlayerRepository repo;

    public Player find(long id) { return repo.findById(id); }
}
JAVA
