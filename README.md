# phpstorm-nav

Direct CLI for JetBrains Serena Plugin - PHP code navigation and refactoring without MCP overhead.

## Requirements

- PhpStorm with [Serena plugin](https://plugins.jetbrains.com/plugin/28946-serena/) installed (~$5/mo)
- Project open in PhpStorm

## Installation

```bash
/plugin install phpstorm-nav@sebastian-marketplace
```

The plugin automatically:
- Creates `phpstorm-nav` command in `~/.local/bin`
- Adds Claude permission for the command

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

## Why This Plugin?

Bypasses Serena's MCP layer for faster, lighter PHP navigation:
- **Direct HTTP** to JetBrains plugin (no JSON-RPC/SSE)
- **Zero dependencies** (Python stdlib only)
- **Less context** (no MCP tool schemas)

## Components

- **Skills**: PHP navigation guidance (`skills/phpstorm-nav/`)
- **Hooks**: Auto-setup on session start (`hooks/`)
- **CLI**: The `phpstorm-nav` command (`bin/`)
