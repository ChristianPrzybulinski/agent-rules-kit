---
description: An error question gets the fix first, the error text byte-for-byte and little prose.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Why does this fail and how do I fix it?

```
$ python3 tools/build.py
  File "tools/build.py", line 12
    print "building"
          ^
SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)?
```
