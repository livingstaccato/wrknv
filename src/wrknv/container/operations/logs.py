#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Container Logs Operations
=========================
Stream and retrieve container logs."""

from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta

from attrs import define
from provide.foundation import logger
from provide.foundation.process import ProcessError, stream
from provide.foundation.time import provide_now
from rich.console import Console

from wrknv.container.runtime.base import ContainerRuntime


@define
class ContainerLogs:
    """Handles container log operations."""

    runtime: ContainerRuntime
    container_name: str
    console: Console

    def get_logs(
        self,
        follow: bool,
        tail: int | None,
        since: str | None,
        timestamps: bool,
    ) -> str | None:
        """Get container logs.

        Args:
            follow: Follow log output
            tail: Number of lines to tail
            since: Show logs since timestamp (e.g., "2023-01-01T00:00:00")
            timestamps: Show timestamps

        Returns:
            Log output if not following, None if following
        """
        try:
            if follow:
                # Stream logs
                for line in self.stream_logs(
                    tail=tail,
                    since=since,
                    timestamps=timestamps,
                ):
                    self.console.print(line, end="")
                return None
            else:
                # Get logs as string
                result = self.runtime.get_container_logs(
                    name=self.container_name,
                    follow=False,
                    tail=tail,
                    since=since,
                )
                return result.stdout

        except ProcessError as e:
            logger.error(
                "Failed to get logs",
                container=self.container_name,
                error=str(e),
            )
            self.console.print(f"[red]❌ Failed to get logs: {e}[/red]")
            return None

    def stream_logs(
        self,
        tail: int | None,
        since: str | None,
        timestamps: bool,
    ) -> Generator[str, None, None]:
        """Stream container logs.

        Args:
            tail: Number of lines to tail
            since: Show logs since timestamp
            timestamps: Show timestamps

        Yields:
            Log lines
        """
        cmd = [self.runtime.runtime_command, "logs", "-f"]

        if tail is not None:
            cmd.extend(["--tail", str(tail)])
        if since:
            cmd.extend(["--since", since])
        if timestamps:
            cmd.append("-t")

        cmd.append(self.container_name)

        try:
            yield from stream(cmd)
        except ProcessError as e:
            logger.error(
                "Failed to stream logs",
                container=self.container_name,
                error=str(e),
            )
            self.console.print(f"[red]❌ Log streaming failed: {e}[/red]")

    def show_logs(
        self,
        lines: int | None,
        since_minutes: int | None,
        grep: str | None,
    ) -> None:
        """Show container logs with filtering.

        Args:
            lines: Number of recent lines to show
            since_minutes: Show logs from last N minutes
            grep: Filter logs by pattern
        """
        # Calculate since timestamp if needed
        since = None
        if since_minutes:
            since_time = provide_now() - timedelta(minutes=since_minutes)
            since = since_time.isoformat()

        # Get logs
        logs = self.get_logs(
            follow=False,
            tail=lines,
            since=since,
            timestamps=False,
        )

        if not logs:
            self.console.print(f"[yellow]No logs found for {self.container_name}[/yellow]")
            return

        # Filter if grep provided
        if grep:
            filtered_lines = []
            for line in logs.splitlines():
                if grep.lower() in line.lower():
                    filtered_lines.append(line)
            logs = "\n".join(filtered_lines)

        # Display logs
        if logs:
            self.console.print(logs)
        else:
            self.console.print("[yellow]No matching logs found[/yellow]")

    def clear_logs(self) -> bool:
        """Clear container logs (if supported by runtime).

        Returns:
            True if successful
        """
        try:
            from provide.foundation.process import run

            # Docker doesn't have a direct clear logs command
            # This is a workaround using truncate
            run(
                [
                    "sh",
                    "-c",
                    f"truncate -s 0 $(docker inspect --format='{{{{.LogPath}}}}' {self.container_name})",
                ],
                check=True,
            )

            logger.info("Container logs cleared", container=self.container_name)
            return True

        except ProcessError as e:
            logger.warning(
                "Failed to clear logs (may not be supported)",
                container=self.container_name,
                error=str(e),
            )
            self.console.print("[yellow]⚠️  Log clearing not supported or failed[/yellow]")
            return False


# 🧰🌍🔚
