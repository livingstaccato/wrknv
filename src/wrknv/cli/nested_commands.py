#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Enhanced command registration with nested group support.

This module extends the Foundation Hub to support nested command groups,
allowing natural CLI structures like `wrknv container status` instead of
`wrknv container-status`."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import inspect
from typing import Any, TypeVar

import click
from provide.foundation import logger
from provide.foundation.hub import get_hub
from provide.foundation.hub.commands import CommandInfo, _extract_click_type

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class CommandGroup:
    """Represents a command group that can contain subcommands."""

    name: str
    description: str | None = None
    commands: dict[str, CommandInfo | CommandGroup] = field(default_factory=dict)
    parent: CommandGroup | None = None
    hidden: bool = False

    def add_command(self, name: str, info: CommandInfo | CommandGroup) -> None:
        """Add a subcommand to this group."""
        self.commands[name] = info
        if isinstance(info, CommandGroup):
            info.parent = self

    def get_command(self, path: list[str]) -> CommandInfo | CommandGroup | None:
        """Get a command by path (e.g., ['container', 'status'])."""
        if not path:
            return self

        name = path[0]
        if name not in self.commands:
            return None

        cmd = self.commands[name]
        if len(path) == 1:
            return cmd

        if isinstance(cmd, CommandGroup):
            return cmd.get_command(path[1:])

        return None

    def to_click_group(self) -> click.Group:
        """Convert this command group to a Click group."""
        group = click.Group(
            name=self.name,
            help=self.description,
            hidden=self.hidden,
        )

        for _cmd_name, cmd_info in self.commands.items():
            if isinstance(cmd_info, CommandGroup):
                # Add subgroup
                subgroup = cmd_info.to_click_group()
                group.add_command(subgroup)
            else:
                # Add command
                click_cmd = self._build_click_command(cmd_info)
                if click_cmd:
                    group.add_command(click_cmd)

        return group

    def _build_click_command(self, info: CommandInfo) -> click.Command | None:
        """Build a Click command from CommandInfo."""
        if info.click_command:
            return info.click_command

        func = info.func
        if not callable(func):
            return None

        # Build Click command from function signature
        sig = inspect.signature(func)
        click_func = func

        # Add parameters as Click options/arguments
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls", "ctx"):
                continue

            has_default = param.default != inspect.Parameter.empty

            if has_default:
                # Create option
                option_name = f"--{param_name.replace('_', '-')}"
                if param.annotation != inspect.Parameter.empty:
                    param_type = _extract_click_type(param.annotation)

                    if param_type is bool:
                        click_func = click.option(
                            option_name,
                            is_flag=True,
                            default=param.default,
                            help=f"{param_name} flag",
                        )(click_func)
                    else:
                        click_func = click.option(
                            option_name,
                            type=param_type,
                            default=param.default,
                            help=f"{param_name} option",
                        )(click_func)
                else:
                    click_func = click.option(
                        option_name,
                        default=param.default,
                        help=f"{param_name} option",
                    )(click_func)
            else:
                # Create argument
                if param.annotation != inspect.Parameter.empty:
                    param_type = _extract_click_type(param.annotation)
                    click_func = click.argument(
                        param_name,
                        type=param_type,
                    )(click_func)
                else:
                    click_func = click.argument(param_name)(click_func)

        return click.Command(
            name=info.name,
            callback=click_func,
            help=info.description,
            hidden=info.hidden,
        )


class NestedCommandRegistry:
    """Registry that supports nested command groups."""

    def __init__(self) -> None:
        self.root = CommandGroup(name="cli", description="CLI root")
        self._flat_registry: dict[str, CommandInfo | CommandGroup] = {}

    def register_command(
        self,
        name: str,
        func: Callable[..., Any] | None = None,
        description: str | None = None,
        group: bool = False,
        parent: str | None = None,
        hidden: bool = False,
        aliases: list[str] | None = None,
    ) -> None:
        """
        Register a command or command group.

        Args:
            name: Command name (can include spaces for nested commands)
            func: Function to execute (None for groups)
            description: Command/group description
            group: Whether this is a command group
            parent: Parent group name (alternative to space-separated name)
            hidden: Whether to hide from help
            aliases: Command aliases
        """
        # Parse the command path
        path = [*parent.split(), name] if parent else name.split()

        # Get or create parent groups
        current = self.root
        for i, part in enumerate(path[:-1]):
            if part not in current.commands:
                # Create intermediate group
                intermediate = CommandGroup(
                    name=part,
                    description=f"{part} commands",
                )
                current.add_command(part, intermediate)
                logger.debug(f"Created intermediate group: {part}")

            cmd = current.commands[part]
            if isinstance(cmd, CommandGroup):
                current = cmd
            else:
                raise ValueError(f"Cannot nest under non-group command: {' '.join(path[: i + 1])}")

        # Register the final command or group
        final_name = path[-1]

        if group or func is None:
            # Register as a group
            cmd_group = CommandGroup(
                name=final_name,
                description=description or f"{final_name} commands",
                hidden=hidden,
            )
            current.add_command(final_name, cmd_group)
            self._flat_registry[" ".join(path)] = cmd_group
            logger.info(f"Registered command group: {' '.join(path)}")
        else:
            # Register as a command
            info = CommandInfo(
                name=final_name,
                func=func,
                description=description or (func.__doc__ if func else None),
                aliases=aliases or [],
                hidden=hidden,
                category=" ".join(path[:-1]) if len(path) > 1 else None,
            )
            current.add_command(final_name, info)
            self._flat_registry[" ".join(path)] = info
            logger.info(f"Registered command: {' '.join(path)}")

    def get_command(self, name: str) -> CommandInfo | CommandGroup | None:
        """Get a command by name (space-separated path)."""
        return self._flat_registry.get(name)

    def to_click_group(self) -> click.Group:
        """Convert the entire registry to a Click group."""
        return self.root.to_click_group()


# Global nested registry
_nested_registry = NestedCommandRegistry()


def register_nested_command(
    name: str,
    *,
    description: str | None = None,
    group: bool = False,
    parent: str | None = None,
    hidden: bool = False,
    aliases: list[str] | None = None,
) -> Callable[[F], F]:
    """
    Register a command with support for nested groups.

    Examples:
        # Register a simple command
        @register_nested_command("status")
        def status():
            pass

        # Register a command group
        @register_nested_command("container", group=True)
        def container_group():
            pass

        # Register a subcommand (two ways)
        @register_nested_command("container status")
        def container_status():
            pass

        # Or using parent parameter
        @register_nested_command("status", parent="container")
        def container_status():
            pass

    Args:
        name: Command name (can be space-separated for nesting)
        description: Command description
        group: Whether this is a command group
        parent: Parent group (alternative to space-separated name)
        hidden: Hide from help
        aliases: Command aliases

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        _nested_registry.register_command(
            name=name,
            func=func if not group else None,
            description=description,
            group=group,
            parent=parent,
            hidden=hidden,
            aliases=aliases,
        )

        # Also register in the Foundation Hub for compatibility
        hub = get_hub()
        full_name = f"{parent} {name}" if parent else name
        flat_name = full_name.replace(" ", "-")

        hub.register(
            name=flat_name,
            value=func,
            dimension="command",
            metadata={
                "nested_path": full_name,
                "is_group": group,
                "description": description,
                "hidden": hidden,
                "aliases": aliases,
            },
        )

        return func

    return decorator


def create_nested_cli(
    name: str = "wrknv",
    version: str = "0.1.0",
    help: str | None = None,
) -> click.Group:
    """
    Create a CLI with nested command groups.

    Args:
        name: CLI name
        version: CLI version
        help: CLI help text

    Returns:
        Click Group with nested commands
    """
    cli = _nested_registry.root.to_click_group()
    cli.name = name

    if help:
        cli.help = help

    # Add version option
    @cli.command(hidden=True)
    @click.option("--version", is_flag=True, help="Show version")
    def version_cmd(version: bool) -> None:
        if version:
            click.echo(f"{name} {version}")

    return cli


def get_nested_registry() -> NestedCommandRegistry:
    """Get the global nested command registry."""
    return _nested_registry


# 🧰🌍🔚
