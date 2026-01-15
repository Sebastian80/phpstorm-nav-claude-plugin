---
name: code-nav
description: "Use when navigating code or refactoring symbols in JetBrains IDEs. Triggers: 'find class', 'find method', 'who calls', 'find usages', 'rename class/method'. Works with all indexed languages."
---

# code-nav: Code Navigation & Refactoring

**Iron Law:** Code symbol navigation = `code-nav`. Not grep. Not glob. Not serena.

Direct HTTP to JetBrains plugin. Zero MCP overhead.

## Commands

```bash
code-nav status                      # Check connection
code-nav find ClassName              # Find symbol
code-nav find ClassName --body       # With source code
code-nav find ClassName --depth 1    # With methods
code-nav refs ClassName              # Find usages
code-nav supertypes ClassName        # Parent classes/interfaces
code-nav subtypes InterfaceName      # Implementations/subclasses
code-nav rename OldName NewName      # IDE refactor (project-wide!)
code-nav overview src/File.php       # File structure
code-nav refresh src/File.php        # Sync with IDE
```

## When to Use

| Task | Command |
|------|---------|
| Find class/method | `find` |
| Who calls this? | `refs` |
| What does this extend? | `supertypes` |
| Who implements this? | `subtypes` |
| Rename symbol | `rename` |
| File structure | `overview` |

## Supported Languages

Works with any language indexed by JetBrains IDEs:
- PHP, JavaScript, TypeScript
- Python, Go, Java, Kotlin
- Ruby, Rust, and more

## When NOT to Use

- **Memory persistence** - Use serena
- **Body replacement edits** - Use serena

## Red Flags - STOP If Thinking This

| Thought | Reality |
|---------|---------|
| "Grep is faster" | code-nav is faster AND accurate |
| "Just this once" | No exceptions to Iron Law |
| "It's urgent" | Urgency makes correct tools MORE important |
| "Simple search" | Simple = perfect for code-nav |

## If Plugin Fails

"Cannot connect" - Ask user to check JetBrains IDE. Do NOT fall back to grep.

## Prerequisites

- JetBrains IDE running with Serena plugin
- Project open in IDE
