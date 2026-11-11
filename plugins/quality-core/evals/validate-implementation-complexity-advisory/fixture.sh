#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository whose feature branch changes a Java method.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p src/main/java/com/example src/test/java
cat > AGENTS.md <<'MD'
# Agents

Test command: `sh run_tests.sh` (compiles with `javac` and runs every `src/test/java/*Test.java`; fails when there is none).
MD
cat > run_tests.sh <<'SH'
#!/bin/sh
set -e
mkdir -p build
javac -d build src/main/java/com/example/*.java src/test/java/*.java
count=0
for t in src/test/java/*Test.java; do
  java -ea -cp build "$(basename "$t" .java)"
  count=$((count + 1))
done
[ "$count" -gt 0 ] || { echo "no tests"; exit 1; }
echo "$count test class(es) passed"
SH
cat > src/main/java/com/example/Fee.java <<'JAVA'
package com.example;

public final class Fee {
    private Fee() {}

    public static int of(int amount) {
        return amount / 100;
    }
}
JAVA
printf 'build/\n' > .gitignore
git add -A
git commit -q -m 'base'
git checkout -q -b feature
cat > src/main/java/com/example/Fee.java <<'JAVA'
package com.example;

public final class Fee {
    private Fee() {}

    public static int of(int amount, String tier, boolean weekend, boolean firstOfMonth) {
        int fee = amount / 100;
        if (amount <= 0) {
            return 0;
        }
        if ("gold".equals(tier)) {
            fee = fee / 2;
        } else if ("silver".equals(tier)) {
            fee = fee * 3 / 4;
        } else if ("staff".equals(tier)) {
            return 0;
        }
        if (weekend && !"gold".equals(tier)) {
            fee += 1;
        }
        if (firstOfMonth || amount > 100_000) {
            fee = Math.max(fee - 2, 0);
        }
        return Math.max(fee, 1);
    }
}
JAVA
cat > src/test/java/FeeTest.java <<'JAVA'
import com.example.Fee;

public class FeeTest {
    public static void main(String[] args) {
        if (Fee.of(10_000, "gold", false, false) != 50) throw new AssertionError("gold halves the fee");
        if (Fee.of(10_000, "staff", true, true) != 0) throw new AssertionError("staff pays nothing");
        if (Fee.of(0, "none", false, false) != 0) throw new AssertionError("no amount, no fee");
    }
}
JAVA
git add -A
git commit -q -m 'feat: fee by tier, weekend and first of month'
