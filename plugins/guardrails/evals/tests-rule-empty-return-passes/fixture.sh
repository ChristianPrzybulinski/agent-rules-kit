#!/usr/bin/env bash
# Scaffold for the eval case: a JUnit test whose assertion passes on a zero return, plus the kit's `tests` rule as the synced copy a project carries in
# .claude/rules/, so Claude Code loads it by path when the case reads a matching file (KIT-080, #275). The rule is read
# from this case's plugin folder; a scaffold that cannot reach it stops instead of testing nothing.
set -euo pipefail
rule="$(dirname "${BASH_SOURCE[0]}")/../../rules/tests.md"
[[ -f "$rule" ]] || { echo "fixture: kit rule $rule not reachable from the scaffold" >&2; exit 1; }
git init -q -b main .
mkdir -p .claude/rules
cp "$rule" .claude/rules/guardrails-tests.md
mkdir -p src/test/java/game
cat > src/test/java/game/PriceCalculatorTest.java <<'JAVA'
package game;

import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class PriceCalculatorTest {
    @Test
    void totalIsComputed() {
        var calc = new PriceCalculator(new FixedTaxRate(0.10));
        long total = calc.total(List.of(new Line("sword", 2, 1500)));
        assertTrue(total >= 0);
    }
}
JAVA
