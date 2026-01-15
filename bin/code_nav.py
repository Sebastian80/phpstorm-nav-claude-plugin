#!/usr/bin/env python3
"""
code-nav: Direct CLI for JetBrains Serena Plugin.

Provides code navigation and refactoring capabilities by communicating
directly with the JetBrains IDE plugin via HTTP API.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# Constants
# =============================================================================

BASE_PORT = 0x5EA2  # 24226
MAX_PORT_SCAN = 20
REQUEST_TIMEOUT = 120

EXIT_SUCCESS = 0
EXIT_ERROR = 1


# =============================================================================
# Data Transfer Objects
# =============================================================================

@dataclass
class Symbol:
    """Represents a code symbol from the JetBrains IDE."""
    name_path: str = ""
    relative_path: str = ""
    kind: str = ""
    line: int | None = None
    body: str | None = None
    children: list[Symbol] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Symbol:
        """Create a Symbol from API response dictionary."""
        text_range = data.get("textRange", {})
        start_pos = text_range.get("startPos", {})

        children = [
            cls.from_dict(child)
            for child in data.get("children", [])
        ]

        return cls(
            name_path=data.get("namePath", ""),
            relative_path=data.get("relativePath", ""),
            kind=data.get("type", data.get("kind", "?")),
            line=start_pos.get("line") or data.get("line"),
            body=data.get("body"),
            children=children,
        )

    @property
    def name(self) -> str:
        """Extract short name from full path."""
        return self.name_path.split("/")[-1] if self.name_path else "?"

    @property
    def location(self) -> str:
        """Format location as path:line."""
        if self.line:
            return f"{self.relative_path}:{self.line}"
        return self.relative_path


@dataclass
class HierarchyItem:
    """Represents an item in a type hierarchy (supertypes/subtypes)."""
    symbol: Symbol
    children: list[HierarchyItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HierarchyItem:
        """Create a HierarchyItem from API response dictionary."""
        symbol = Symbol.from_dict(data.get("symbol", {}))
        children = [
            cls.from_dict(child)
            for child in data.get("children", [])
        ]
        return cls(symbol=symbol, children=children)


# =============================================================================
# Exceptions
# =============================================================================

class PluginConnectionError(Exception):
    """Raised when unable to connect to the JetBrains plugin."""
    pass


class SymbolNotFoundError(Exception):
    """Raised when a symbol cannot be found."""
    pass


# =============================================================================
# JetBrains Plugin Client
# =============================================================================

class JetBrainsClient:
    """HTTP client for communicating with the JetBrains Serena plugin."""

    def __init__(self, port: int) -> None:
        self.base_url = f"http://127.0.0.1:{port}"

    def _request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the plugin.

        Args:
            endpoint: API endpoint path (e.g., "/findSymbol")
            data: Optional JSON payload for POST requests

        Returns:
            Parsed JSON response

        Raises:
            urllib.error.URLError: On connection failure
            urllib.error.HTTPError: On HTTP error response
        """
        url = f"{self.base_url}{endpoint}"

        if data is not None:
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
        else:
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json"},
                method="GET",
            )

        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))

    def status(self) -> dict[str, Any]:
        """Get plugin status including project root and version."""
        return self._request("/status")

    def find_symbol(
        self,
        name_path: str,
        relative_path: str | None = None,
        include_body: bool = False,
        depth: int = 0,
        search_deps: bool = False,
    ) -> list[Symbol]:
        """
        Find symbols by name.

        Args:
            name_path: Symbol name or path to search for
            relative_path: Optional file path to restrict search
            include_body: Include source code in results
            depth: Depth of children to include (0=none, 1=direct, etc.)
            search_deps: Search in vendor/node_modules

        Returns:
            List of matching symbols
        """
        response = self._request("/findSymbol", {
            "namePath": name_path,
            "relativePath": relative_path,
            "includeBody": include_body,
            "depth": depth,
            "includeLocation": True,
            "searchDeps": search_deps,
        })
        return [Symbol.from_dict(s) for s in response.get("symbols", [])]

    def find_references(self, name_path: str, relative_path: str) -> list[Symbol]:
        """
        Find all references to a symbol.

        Args:
            name_path: Full symbol path
            relative_path: File containing the symbol

        Returns:
            List of referencing symbols
        """
        response = self._request("/findReferences", {
            "namePath": name_path,
            "relativePath": relative_path,
        })
        return [Symbol.from_dict(s) for s in response.get("symbols", [])]

    def get_overview(self, relative_path: str, depth: int = 1) -> list[Symbol]:
        """
        Get symbol structure of a file.

        Args:
            relative_path: File path to analyze
            depth: Depth of symbol hierarchy to return

        Returns:
            List of top-level symbols with children
        """
        response = self._request("/getSymbolsOverview", {
            "relativePath": relative_path,
            "depth": depth,
        })
        return [Symbol.from_dict(s) for s in response.get("symbols", [])]

    def get_supertypes(
        self,
        name_path: str,
        relative_path: str,
        depth: int | None = None,
    ) -> tuple[Symbol | None, list[HierarchyItem]]:
        """
        Get parent classes, interfaces, and traits.

        Args:
            name_path: Symbol to get supertypes for
            relative_path: File containing the symbol
            depth: Maximum traversal depth

        Returns:
            Tuple of (base symbol, list of supertype hierarchy items)
        """
        data: dict[str, Any] = {
            "namePath": name_path,
            "relativePath": relative_path,
        }
        if depth is not None:
            data["depth"] = depth

        response = self._request("/getSupertypes", data)

        base_symbol = None
        if "symbol" in response:
            base_symbol = Symbol.from_dict(response["symbol"])

        hierarchy = [
            HierarchyItem.from_dict(item)
            for item in response.get("hierarchy", [])
        ]
        return base_symbol, hierarchy

    def get_subtypes(
        self,
        name_path: str,
        relative_path: str,
        depth: int | None = None,
    ) -> tuple[Symbol | None, list[HierarchyItem]]:
        """
        Get subclasses and implementations.

        Args:
            name_path: Symbol to get subtypes for
            relative_path: File containing the symbol
            depth: Maximum traversal depth

        Returns:
            Tuple of (base symbol, list of subtype hierarchy items)
        """
        data: dict[str, Any] = {
            "namePath": name_path,
            "relativePath": relative_path,
        }
        if depth is not None:
            data["depth"] = depth

        response = self._request("/getSubtypes", data)

        base_symbol = None
        if "symbol" in response:
            base_symbol = Symbol.from_dict(response["symbol"])

        hierarchy = [
            HierarchyItem.from_dict(item)
            for item in response.get("hierarchy", [])
        ]
        return base_symbol, hierarchy

    def rename_symbol(
        self,
        name_path: str,
        relative_path: str,
        new_name: str,
        rename_in_comments: bool = False,
        rename_in_text: bool = False,
    ) -> dict[str, Any]:
        """
        Rename a symbol across the codebase.

        Args:
            name_path: Symbol to rename
            relative_path: File containing the symbol
            new_name: New name for the symbol
            rename_in_comments: Also rename occurrences in comments
            rename_in_text: Also rename occurrences in strings/text

        Returns:
            API response
        """
        return self._request("/renameSymbol", {
            "namePath": name_path,
            "relativePath": relative_path,
            "newName": new_name,
            "renameInComments": rename_in_comments,
            "renameInTextOccurrences": rename_in_text,
        })

    def refresh_file(self, relative_path: str) -> dict[str, Any]:
        """
        Force IDE to reload a file.

        Args:
            relative_path: File path to refresh

        Returns:
            API response
        """
        return self._request("/refreshFile", {"relativePath": relative_path})


# =============================================================================
# Plugin Discovery
# =============================================================================

def find_plugin() -> JetBrainsClient | None:
    """
    Scan ports to find a running JetBrains plugin instance.

    Returns:
        Connected client or None if not found
    """
    for port in range(BASE_PORT, BASE_PORT + MAX_PORT_SCAN):
        try:
            client = JetBrainsClient(port)
            client.status()
            return client
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError, OSError):
            continue
    return None


def get_client_or_exit() -> JetBrainsClient:
    """
    Get a connected client or exit with error.

    Returns:
        Connected JetBrainsClient

    Raises:
        SystemExit: If no plugin connection can be established
    """
    client = find_plugin()
    if not client:
        print("Error: Cannot connect to JetBrains plugin", file=sys.stderr)
        print("Make sure your IDE is running with the Serena plugin.", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    return client


# =============================================================================
# Output Formatting
# =============================================================================

def format_symbol(symbol: Symbol, indent: int = 0) -> str:
    """
    Format a symbol for display.

    Args:
        symbol: Symbol to format
        indent: Indentation level

    Returns:
        Formatted string representation
    """
    prefix = "  " * indent
    lines = [f"{prefix}{symbol.kind:12} {symbol.name:40} {symbol.location}"]

    if symbol.body:
        separator = f"{prefix}{'─' * 60}"
        lines.append(separator)

        body_lines = symbol.body.split("\n")[:30]
        for line in body_lines:
            lines.append(f"{prefix}  {line}")

        if symbol.body.count("\n") > 30:
            lines.append(f"{prefix}  ... (truncated)")

        lines.append(separator)

    for child in symbol.children:
        lines.append(format_symbol(child, indent + 1))

    return "\n".join(lines)


def format_hierarchy(items: list[HierarchyItem], indent: int = 0) -> str:
    """
    Format a type hierarchy for display.

    Args:
        items: Hierarchy items to format
        indent: Indentation level

    Returns:
        Formatted string representation
    """
    lines = []
    for item in items:
        prefix = "  " * indent
        sym = item.symbol
        lines.append(f"{prefix}{sym.kind:12} {sym.name_path:40} {sym.relative_path}")

        if item.children:
            lines.append(format_hierarchy(item.children, indent + 1))

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================

def cmd_status(args: argparse.Namespace) -> int:
    """Handle 'status' command."""
    client = get_client_or_exit()
    result = client.status()
    print(f"Connected to JetBrains plugin at {client.base_url}")
    print(f"Project root: {result.get('projectRoot', '?')}")
    return EXIT_SUCCESS


def cmd_find(args: argparse.Namespace) -> int:
    """Handle 'find' command."""
    if not args.pattern or not args.pattern.strip():
        print("Error: Symbol pattern required", file=sys.stderr)
        return EXIT_ERROR

    client = get_client_or_exit()
    symbols = client.find_symbol(
        args.pattern,
        args.path,
        args.body,
        args.depth,
        args.deps,
    )

    if not symbols:
        print(f"No symbols found for: {args.pattern}", file=sys.stderr)
        return EXIT_ERROR

    print(f"Found {len(symbols)} symbol(s):\n")
    for symbol in symbols:
        print(format_symbol(symbol))
        print()

    return EXIT_SUCCESS


def cmd_refs(args: argparse.Namespace) -> int:
    """Handle 'refs' command."""
    if not args.pattern or not args.pattern.strip():
        print("Error: Symbol pattern required", file=sys.stderr)
        return EXIT_ERROR

    client = get_client_or_exit()

    # First find the symbol
    symbols = client.find_symbol(args.pattern)
    if not symbols:
        print(f"Symbol not found: {args.pattern}", file=sys.stderr)
        return EXIT_ERROR

    symbol = symbols[0]
    refs = client.find_references(symbol.name_path, symbol.relative_path)

    if not refs:
        print(f"No references found for: {args.pattern}")
        return EXIT_SUCCESS

    print(f"Found {len(refs)} reference(s) to {args.pattern}:\n")
    for ref in refs:
        print(format_symbol(ref))
        print()

    return EXIT_SUCCESS


def cmd_overview(args: argparse.Namespace) -> int:
    """Handle 'overview' command."""
    client = get_client_or_exit()
    symbols = client.get_overview(args.path, args.depth)

    if not symbols:
        print(f"No symbols in: {args.path}", file=sys.stderr)
        return EXIT_ERROR

    print(f"Symbols in {args.path}:\n")
    for symbol in symbols:
        print(format_symbol(symbol))
        print()

    return EXIT_SUCCESS


def cmd_supertypes(args: argparse.Namespace) -> int:
    """Handle 'supertypes' command."""
    if not args.pattern or not args.pattern.strip():
        print("Error: Symbol pattern required", file=sys.stderr)
        return EXIT_ERROR

    client = get_client_or_exit()

    # First find the symbol
    symbols = client.find_symbol(args.pattern)
    if not symbols:
        print(f"Symbol not found: {args.pattern}", file=sys.stderr)
        return EXIT_ERROR

    symbol = symbols[0]
    base_symbol, hierarchy = client.get_supertypes(
        symbol.name_path,
        symbol.relative_path,
        args.depth,
    )

    if not hierarchy:
        print(f"No supertypes found for: {args.pattern}")
        return EXIT_SUCCESS

    name = base_symbol.name_path if base_symbol else args.pattern
    print(f"Supertypes of {name}:\n")
    print(format_hierarchy(hierarchy))

    return EXIT_SUCCESS


def cmd_subtypes(args: argparse.Namespace) -> int:
    """Handle 'subtypes' command."""
    if not args.pattern or not args.pattern.strip():
        print("Error: Symbol pattern required", file=sys.stderr)
        return EXIT_ERROR

    client = get_client_or_exit()

    # First find the symbol
    symbols = client.find_symbol(args.pattern)
    if not symbols:
        print(f"Symbol not found: {args.pattern}", file=sys.stderr)
        return EXIT_ERROR

    symbol = symbols[0]
    base_symbol, hierarchy = client.get_subtypes(
        symbol.name_path,
        symbol.relative_path,
        args.depth,
    )

    if not hierarchy:
        print(f"No subtypes found for: {args.pattern}")
        return EXIT_SUCCESS

    name = base_symbol.name_path if base_symbol else args.pattern
    print(f"Subtypes of {name}:\n")
    print(format_hierarchy(hierarchy))

    return EXIT_SUCCESS


def cmd_rename(args: argparse.Namespace) -> int:
    """Handle 'rename' command."""
    client = get_client_or_exit()

    # First find the symbol
    symbols = client.find_symbol(args.symbol)
    if not symbols:
        print(f"Symbol not found: {args.symbol}", file=sys.stderr)
        return EXIT_ERROR

    if len(symbols) > 1:
        print(f"Multiple symbols found for '{args.symbol}':", file=sys.stderr)
        for i, sym in enumerate(symbols):
            print(f"  [{i}] {sym.relative_path}", file=sys.stderr)
        print("\nUse --path to specify which one.", file=sys.stderr)
        return EXIT_ERROR

    symbol = symbols[0]
    print(f"Renaming {symbol.name_path} -> {args.new_name}")
    print(f"  in: {symbol.relative_path}")

    try:
        client.rename_symbol(
            symbol.name_path,
            symbol.relative_path,
            args.new_name,
            args.comments,
            args.text,
        )
        print("Rename successful!")
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Rename failed: {e}", file=sys.stderr)
        return EXIT_ERROR


def cmd_refresh(args: argparse.Namespace) -> int:
    """Handle 'refresh' command."""
    client = get_client_or_exit()

    try:
        client.refresh_file(args.path)
        print(f"Refreshed: {args.path}")
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Refresh failed: {e}", file=sys.stderr)
        return EXIT_ERROR


# =============================================================================
# Argument Parser
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="code-nav",
        description="Direct CLI for JetBrains Serena Plugin - code navigation and refactoring",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser(
        "status",
        help="Check plugin connection",
    )

    # find
    p_find = subparsers.add_parser(
        "find",
        help="Find symbol by name",
    )
    p_find.add_argument("pattern", help="Symbol name to search for")
    p_find.add_argument("--path", "-p", help="Restrict search to file path")
    p_find.add_argument("--body", "-b", action="store_true", help="Include source code")
    p_find.add_argument("--depth", "-d", type=int, default=0, help="Include children (depth levels)")
    p_find.add_argument("--deps", action="store_true", help="Search in dependencies")

    # refs
    p_refs = subparsers.add_parser(
        "refs",
        help="Find references to a symbol",
    )
    p_refs.add_argument("pattern", help="Symbol name to find references for")

    # overview
    p_overview = subparsers.add_parser(
        "overview",
        help="Show file symbol structure",
    )
    p_overview.add_argument("path", help="File path to analyze")
    p_overview.add_argument("--depth", "-d", type=int, default=1, help="Symbol hierarchy depth")

    # supertypes
    p_supertypes = subparsers.add_parser(
        "supertypes",
        help="Get parent classes/interfaces",
    )
    p_supertypes.add_argument("pattern", help="Symbol name")
    p_supertypes.add_argument("--depth", "-d", type=int, default=None, help="Traversal depth")

    # subtypes
    p_subtypes = subparsers.add_parser(
        "subtypes",
        help="Get subclasses/implementations",
    )
    p_subtypes.add_argument("pattern", help="Symbol name")
    p_subtypes.add_argument("--depth", "-d", type=int, default=None, help="Traversal depth")

    # rename
    p_rename = subparsers.add_parser(
        "rename",
        help="Rename symbol (IDE refactoring)",
    )
    p_rename.add_argument("symbol", help="Symbol to rename")
    p_rename.add_argument("new_name", help="New name")
    p_rename.add_argument("--path", "-p", help="Specify file if multiple matches")
    p_rename.add_argument("--comments", "-c", action="store_true", help="Rename in comments")
    p_rename.add_argument("--text", "-t", action="store_true", help="Rename in text occurrences")

    # refresh
    p_refresh = subparsers.add_parser(
        "refresh",
        help="Refresh file in IDE",
    )
    p_refresh.add_argument("path", help="File path to refresh")

    return parser


# =============================================================================
# Command Dispatch
# =============================================================================

COMMANDS = {
    "status": cmd_status,
    "find": cmd_find,
    "refs": cmd_refs,
    "overview": cmd_overview,
    "supertypes": cmd_supertypes,
    "subtypes": cmd_subtypes,
    "rename": cmd_rename,
    "refresh": cmd_refresh,
}


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    handler = COMMANDS.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return EXIT_ERROR

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
