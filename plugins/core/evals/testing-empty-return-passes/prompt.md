---
description: A test that passes when the function returns zero is rewritten with the expected value.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this JUnit test before I merge it. `PriceCalculator.total` is new in this PR.

```java
@Test
void totalIsComputed() {
    var calc = new PriceCalculator(new FixedTaxRate(0.10));
    long total = calc.total(List.of(new Line("sword", 2, 1500)));
    assertTrue(total >= 0);
}
```
