# code-nav

Direct CLI for JetBrains Serena Plugin - code navigation and refactoring without MCP overhead.

## Requirements

- JetBrains IDE (PhpStorm, WebStorm, IntelliJ, PyCharm, etc.) with [Serena plugin](https://plugins.jetbrains.com/plugin/28946-serena/) installed (~$5/mo)
- Project open in the IDE

## Installation

```bash
/plugin install code-nav@sebastian-marketplace
```

The plugin automatically:
- Creates `code-nav` command in `~/.local/bin`
- Adds Claude permission for the command

## Commands

```bash
code-nav status                      # Check connection
code-nav find ClassName              # Find symbol
code-nav find ClassName --body       # With source code
code-nav find ClassName --depth 1    # With methods
code-nav refs ClassName              # Find usages
code-nav rename OldName NewName      # IDE refactor (project-wide!)
code-nav overview src/File.php       # File structure
code-nav refresh src/File.php        # Sync with IDE
```

## Why This Plugin?

Bypasses Serena's MCP layer for faster, lighter code navigation:
- **Direct HTTP** to JetBrains plugin (no JSON-RPC/SSE)
- **Zero dependencies** (Python stdlib only)
- **Less context** (no MCP tool schemas)

## Supported Languages

Works with any language indexed by JetBrains IDEs:
- PHP, JavaScript, TypeScript
- Python, Go, Java, Kotlin
- Ruby, Rust, and more

## Components

- **Skills**: Code navigation guidance (`skills/code-nav/`)
- **Hooks**: Auto-setup on session start (`hooks/`)
- **CLI**: The `code-nav` command (`bin/`)
