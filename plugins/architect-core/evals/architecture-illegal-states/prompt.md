---
description: An aggregate with status strings and nullable fields becomes types that cannot hold an illegal state.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

I'm defining the `Order` aggregate for the shop. Review this model before I build on it.

```java
public class Order {
    public String status;          // "OPEN", "PAID", "SHIPPED", "CANCELLED"
    public Instant paidAt;         // set when PAID or SHIPPED
    public String trackingCode;    // set only when SHIPPED
    public String cancelReason;    // set only when CANCELLED
}
```
