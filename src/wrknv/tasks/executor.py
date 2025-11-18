#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Task Executor

Executes task commands and captures results using provide.foundation process APIs."""

from __future__ import annotations

from pathlib import Path
import shlex
import sys
import time

from attrs import define
from provide.foundation import logger
from provide.foundation.errors import ProcessError, ProcessTimeoutError
from provide.foundation.process import async_run, async_stream

from wrknv.errors import TaskTimeoutError

from .environment import ExecutionEnvironment, ExecutionMode
from .schema import TaskConfig, TaskResult


def format_task_title(task: TaskConfig) -> str:
    """Format task name for process title based on configured format.

    Args:
        task: Task configuration

    Returns:
        Formatted task name string

    Examples:
        >>> task = TaskConfig(name="coverage", namespace="test.unit", process_title_format="full")
        >>> format_task_title(task)
        "test.unit.coverage"

        >>> task = TaskConfig(name="coverage", namespace="test.unit", process_title_format="leaf")
        >>> format_task_title(task)
        "coverage"

        >>> task = TaskConfig(name="coverage", namespace="test.unit", process_title_format="abbreviated")
        >>> format_task_title(task)
        "test...coverage"
    """
    full_name = task.full_name
    fmt = task.process_title_format

    if fmt == "leaf":
        # Return only the leaf (last part)
        return task.name

    if fmt == "abbreviated":
        # Return first...last for nested tasks
        if task.namespace:
            parts = full_name.split(".")
            if len(parts) <= 2:
                # Not deep enough to abbreviate
                return full_name
            # Show first and last with ellipsis
            return f"{parts[0]}...{parts[-1]}"
        return full_name

    # Default: "full" - return complete namespaced name
    return full_name


def _should_stream_output(task: TaskConfig) -> bool:
    """Determine if task output should be streamed in real-time.

    Streaming is enabled when:
    1. Task explicitly sets stream_output=True, OR
    2. stdout is a TTY (interactive terminal)

    Args:
        task: Task configuration

    Returns:
        True if output should be streamed, False if buffered
    """
    # Explicit config takes precedence
    if task.stream_output:
        return True

    # Auto-detect: stream if stdout is a TTY (interactive terminal)
    return sys.stdout.isatty()


@define
class TaskExecutor:
    """Executes tasks defined in wrknv.toml using provide-foundation process APIs."""

    repo_path: Path
    env: dict[str, str] | None = None
    default_timeout: float = 300.0  # 5 minute default timeout
    package_name: str | None = None
    execution_mode: ExecutionMode = "auto"
    auto_detect_env: bool = True
    execution_env: ExecutionEnvironment | None = None

    def __attrs_post_init__(self) -> None:
        """Initialize execution environment after attrs creates instance."""
        if self.auto_detect_env:
            object.__setattr__(
                self,
                "execution_env",
                ExecutionEnvironment(
                    project_dir=self.repo_path,
                    package_name=self.package_name,
                    mode=self.execution_mode,
                ),
            )
            logger.debug(
                "Execution environment initialized",
                venv_path=str(self.execution_env.venv_path)
                if self.execution_env and self.execution_env.venv_path
                else None,
                is_uv_project=self.execution_env.is_uv_project if self.execution_env else False,
                package_is_editable=self.execution_env.package_is_editable if self.execution_env else False,
                use_uv_run=self.execution_env.use_uv_run if self.execution_env else False,
            )

    async def execute(
        self,
        task: TaskConfig,
        args: list[str] | None = None,
        dry_run: bool = False,
    ) -> TaskResult:
        """Execute a single task.

        Args:
            task: Task to execute
            args: Optional arguments to append to the command
            dry_run: If True, show what would be executed without running

        Returns:
            TaskResult with execution details
        """
        # Build the command with args
        if isinstance(task.run, str):
            command = task.run
            if args:
                # Append args with proper shell quoting
                quoted_args = " ".join(shlex.quote(arg) for arg in args)
                command = f"{command} {quoted_args}"
        else:
            # Composite tasks should be handled by registry
            msg = "Composite tasks should be handled by registry"
            raise NotImplementedError(msg)

        # Apply execution environment command preparation (uv run prefix, etc.)
        if self.execution_env:
            command = self.execution_env.prepare_command(
                command=command,
                prefix_override=task.command_prefix,
            )
            logger.debug(
                "Command prepared",
                task=task.full_name,
                final_command=command[:100] + "..." if len(command) > 100 else command,
                use_uv_run=self.execution_env.use_uv_run,
            )
        elif task.command_prefix is not None:
            # Apply per-task prefix even without ExecutionEnvironment
            if task.command_prefix:  # Non-empty string
                command = f"{task.command_prefix} {command}"
            logger.debug(
                "Per-task command prefix applied",
                task=task.full_name,
                prefix=task.command_prefix,
            )

        if dry_run:
            logger.info(
                "Dry run task",
                task=task.full_name,
                command=command,
                cwd=str(task.working_dir or self.repo_path),
            )
            return TaskResult(
                task=task,
                success=True,
                exit_code=0,
                stdout="",
                stderr="",
                duration=0.0,
            )

        # Determine working directory
        cwd = task.working_dir or self.repo_path
        timeout = task.timeout or self.default_timeout

        # Log task start
        logger.info(
            "Starting task",
            task=task.full_name,
            command=command[:100] + "..." if len(command) > 100 else command,
            cwd=str(cwd),
            timeout=timeout,
        )

        # Set parent process title
        from provide.foundation.process import set_process_title

        formatted_task_name = format_task_title(task)
        set_process_title(f"we: {formatted_task_name}")

        # Build environment: merge executor env with task env
        exec_env = {}
        if self.env:
            exec_env.update(self.env)
        exec_env.update(task.env)

        # Apply execution environment preparation (PATH modification for venv)
        if self.execution_env:
            exec_env = self.execution_env.prepare_environment(base_env=exec_env)
            logger.trace(
                "Environment prepared",
                task=task.full_name,
                path_modified=self.execution_env.venv_path is not None and not self.execution_env.use_uv_run,
            )

        # Determine if we should stream output
        use_streaming = _should_stream_output(task)

        if use_streaming:
            logger.debug(
                "Streaming enabled",
                task=task.full_name,
                explicit_config=task.stream_output,
                tty_detected=sys.stdout.isatty(),
            )

        # Execute command using foundation's async_run or async_stream
        start = time.time()

        try:
            if use_streaming:
                # Streaming mode: show output in real-time using chunk-based streaming
                # Parse shell command into list for async_stream
                # Use shlex.split() to properly parse quoted args, shell features, etc.
                try:
                    cmd_list = shlex.split(command)
                except ValueError:
                    # If shlex fails (complex shell), fall back to sh -c wrapper
                    cmd_list = ["/bin/sh", "-c", command]

                # Add PYTHONUNBUFFERED to force immediate output from Python subprocesses
                stream_env = exec_env.copy() if exec_env else {}
                stream_env["PYTHONUNBUFFERED"] = "1"

                stdout_chunks = []

                async for chunk in async_stream(
                    cmd=cmd_list,
                    cwd=cwd,
                    env=stream_env,
                    timeout=timeout,
                    stream_stderr=True,  # Merge stderr into stdout for streaming
                    print_output=True,  # Print chunks immediately to stdout
                    process_title=formatted_task_name,  # Set child process title
                ):
                    # Accumulate chunks for TaskResult
                    stdout_chunks.append(chunk)

                duration = time.time() - start

                # async_stream doesn't provide exit code, assume success if no exception
                exit_code = 0
                stdout_text = "".join(stdout_chunks)
                stderr_text = ""  # Merged into stdout

                logger.info(
                    "Task completed",
                    task=task.full_name,
                    success=True,
                    duration=f"{duration:.2f}s",
                    exit_code=exit_code,
                )

                return TaskResult(
                    task=task,
                    success=True,
                    exit_code=exit_code,
                    stdout=stdout_text,
                    stderr=stderr_text,
                    duration=duration,
                )
            else:
                # Buffered mode: capture all output (original behavior)
                result = await async_run(
                    cmd=command,
                    cwd=cwd,
                    env=exec_env if exec_env else None,  # Foundation merges with os.environ
                    capture_output=True,
                    check=False,  # We handle errors ourselves
                    timeout=timeout,
                    shell=True,  # Explicit shell usage for command strings
                    process_title=formatted_task_name,  # Set child process title
                )

                duration = time.time() - start

                # Log task completion
                logger.info(
                    "Task completed",
                    task=task.full_name,
                    success=result.returncode == 0,
                    duration=f"{duration:.2f}s",
                    exit_code=result.returncode,
                )

                return TaskResult(
                    task=task,
                    success=result.returncode == 0,
                    exit_code=result.returncode,
                    stdout=result.stdout or "",
                    stderr=result.stderr or "",
                    duration=duration,
                )

        except KeyboardInterrupt:
            duration = time.time() - start
            logger.info(
                "Task interrupted by user",
                task=task.full_name,
                duration=f"{duration:.2f}s",
            )
            # Re-raise to allow graceful shutdown
            raise

        except ProcessTimeoutError as e:
            duration = time.time() - start
            logger.error(
                "Task timeout",
                task=task.full_name,
                timeout=timeout,
                duration=f"{duration:.2f}s",
            )

            # Raise task-specific timeout error
            raise TaskTimeoutError(task.full_name, timeout) from e

        except ProcessError as e:
            duration = time.time() - start
            logger.error(
                "Task execution failed",
                task=task.full_name,
                exit_code=e.exit_code if hasattr(e, "exit_code") else 1,
                duration=f"{duration:.2f}s",
                error=str(e),
            )

            # Return error result instead of raising (for non-critical failures)
            return TaskResult(
                task=task,
                success=False,
                exit_code=e.exit_code if hasattr(e, "exit_code") else 1,
                stdout="",
                stderr=str(e),
                duration=duration,
            )
