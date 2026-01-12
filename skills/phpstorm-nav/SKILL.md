---
name: phpstorm-nav
description: "Use when navigating PHP code or refactoring PHP symbols. Triggers: 'find class', 'find method', 'who calls', 'find usages', 'rename class/method'. PHP ONLY - not for JS/Twig/YAML."
---

# phpstorm-nav: PHP Code Navigation & Refactoring

**Iron Law:** PHP navigation = `phpstorm-nav`. Not grep. Not glob. Not serena.

Direct HTTP to JetBrains plugin. Zero MCP overhead.

## Commands

```bash
phpstorm-nav status                      # Check connection
phpstorm-nav find ClassName              # Find symbol
phpstorm-nav find ClassName --body       # With source code
phpstorm-nav find ClassName --depth 1    # With methods
phpstorm-nav refs ClassName              # Find usages
phpstorm-nav rename OldName NewName      # IDE refactor (project-wide!)
phpstorm-nav overview src/File.php       # File structure
phpstorm-nav refresh src/File.php        # Sync with IDE
```

## When to Use

| Task | Command |
|------|---------|
| Find PHP class/method | `find` |
| Who calls this? | `refs` |
| Rename symbol | `rename` |
| File structure | `overview` |

## When NOT to Use

- **JavaScript/Twig/YAML** → Use grep
- **Memory persistence** → Use serena
- **Body replacement edits** → Use serena

## Red Flags - STOP If Thinking This

| Thought | Reality |
|---------|---------|
| "Grep is faster" | phpstorm-nav is faster AND accurate |
| "Just this once" | No exceptions to Iron Law |
| "It's urgent" | Urgency makes correct tools MORE important |
| "Simple search" | Simple = perfect for phpstorm-nav |

## If Plugin Fails

"Cannot connect" → Ask user to check PhpStorm. Do NOT fall back to grep.

## Prerequisites

- PhpStorm running with Serena plugin
- Project open in IDE
