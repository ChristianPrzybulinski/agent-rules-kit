---
description: Field injection is replaced by constructor injection.
tags: [ready]
plugins: [../.., ../../../core]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Review this Spring service and fix the injection:

```java
@Service
public class PlayerService {
    @Autowired
    private PlayerRepository repo;
    public Player find(long id) { return repo.findById(id); }
}
```
