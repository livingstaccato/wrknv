#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# ruff: noqa: E501

"""Shell Completion Generation
===========================
Generate shell completion scripts for various shells."""

from __future__ import annotations


def generate_completions(shell: str) -> str:
    """Generate shell completion script for the specified shell.

    Args:
        shell: Shell type ('bash', 'zsh', or 'fish')

    Returns:
        Completion script as a string
    """
    if shell == "bash":
        return generate_bash_completions()
    elif shell == "zsh":
        return generate_zsh_completions()
    elif shell == "fish":
        return generate_fish_completions()
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def generate_bash_completions() -> str:
    """Generate Bash completion script."""
    return """# Bash completion for wrknv
_wrknv_completion() {
    local cur prev words cword
    _init_completion || return

    local commands="setup tf status sync generate-env container profile config package"
    local setup_opts="--init --shell-integration --force --check --completions --install --help"
    local tf_opts="--latest --list --dry-run --terraform --help"
    local container_commands="build start enter stop restart status logs clean rebuild"
    local profile_commands="list save load show delete export import"
    local config_commands="show edit validate init get set path"
    local package_commands="build verify keygen clean init list info sign publish config"

    case "${prev}" in
        wrknv)
            COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
            return 0
            ;;
        setup)
            COMPREPLY=($(compgen -W "${setup_opts}" -- "${cur}"))
            return 0
            ;;
        tf)
            COMPREPLY=($(compgen -W "${tf_opts}" -- "${cur}"))
            return 0
            ;;
        container)
            COMPREPLY=($(compgen -W "${container_commands}" -- "${cur}"))
            return 0
            ;;
        profile)
            COMPREPLY=($(compgen -W "${profile_commands}" -- "${cur}"))
            return 0
            ;;
        config)
            COMPREPLY=($(compgen -W "${config_commands}" -- "${cur}"))
            return 0
            ;;
        package)
            COMPREPLY=($(compgen -W "${package_commands}" -- "${cur}"))
            return 0
            ;;
        --completions)
            COMPREPLY=($(compgen -W "bash zsh fish" -- "${cur}"))
            return 0
            ;;
    esac

    # File completion for certain options
    case "${prev}" in
        --manifest|--output|-o|--key)
            _filedir
            return 0
            ;;
    esac

    # Default to file completion
    _filedir
}

complete -F _wrknv_completion wrknv
"""


def generate_zsh_completions() -> str:
    """Generate Zsh completion script."""
    return """#compdef wrknv
# Zsh completion for wrknv

_wrknv() {
    local -a commands
    commands=(
        'setup:Set up wrknv environment and integrations'
        'tf:Install or manage Terraform/OpenTofu versions'
        'status:Show status of all managed tools'
        'sync:Install all tools from configuration'
        'generate-env:Generate environment setup script'
        'container:Manage development containers'
        'profile:Manage workenv profiles'
        'config:Manage workenv configuration'
        'package:Manage provider packages'
    )

    local -a setup_options
    setup_options=(
        '--init[Initialize wrknv workenv]'
        '--shell-integration[Set up shell aliases]'
        '--force[Force recreate workenv]'
        '--check[Check system dependencies]'
        '--completions[Generate shell completions]:shell:(bash zsh fish)'
        '--install[Install completions]'
    )

    local -a tf_options
    tf_options=(
        '--latest[Install latest version]'
        '--list[List available versions]'
        '--dry-run[Show what would be installed]'
        '--terraform[Install Terraform instead of OpenTofu]'
    )

    _arguments -C \\
        '1: :->command' \\
        '2: :->subcommand' \\
        '*:: :->args'

    case $state in
        command)
            _describe -t commands 'wrknv command' commands
            ;;
        subcommand)
            case $words[1] in
                container)
                    local -a container_commands
                    container_commands=(
                        'build:Build container image'
                        'start:Start container'
                        'enter:Enter running container'
                        'stop:Stop container'
                        'restart:Restart container'
                        'status:Show container status'
                        'logs:Show container logs'
                        'clean:Remove container and image'
                        'rebuild:Rebuild container from scratch'
                    )
                    _describe -t container_commands 'container command' container_commands
                    ;;
                profile)
                    local -a profile_commands
                    profile_commands=(
                        'list:List available profiles'
                        'save:Save current state as profile'
                        'load:Load profile'
                        'show:Show profile details'
                        'delete:Delete profile'
                        'export:Export profile to file'
                        'import:Import profile from file'
                    )
                    _describe -t profile_commands 'profile command' profile_commands
                    ;;
                config)
                    local -a config_commands
                    config_commands=(
                        'show:Show configuration'
                        'edit:Edit configuration file'
                        'validate:Validate configuration'
                        'init:Initialize new configuration'
                        'get:Get configuration value'
                        'set:Set configuration value'
                        'path:Show configuration file path'
                    )
                    _describe -t config_commands 'config command' config_commands
                    ;;
                package)
                    local -a package_commands
                    package_commands=(
                        'build:Build provider package'
                        'verify:Verify package integrity'
                        'keygen:Generate signing keys'
                        'clean:Clean package cache'
                        'init:Initialize new provider'
                        'list:List built packages'
                        'info:Show package information'
                        'sign:Sign package'
                        'publish:Publish package to registry'
                        'config:Show package configuration'
                    )
                    _describe -t package_commands 'package command' package_commands
                    ;;
            esac
            ;;
        args)
            case $words[1] in
                setup)
                    _arguments $setup_options
                    ;;
                tf)
                    _arguments $tf_options
                    ;;
            esac
            ;;
    esac
}

_wrknv "$@"
"""


def generate_fish_completions() -> str:
    """Generate Fish completion script."""
    return """# Fish completion for wrknv

# Disable file completions by default
complete -c wrknv -f

# Main commands
complete -c wrknv -n "__fish_use_subcommand" -a "setup" -d "Set up wrknv environment"
complete -c wrknv -n "__fish_use_subcommand" -a "tf" -d "Manage Terraform/OpenTofu"
complete -c wrknv -n "__fish_use_subcommand" -a "status" -d "Show tool status"
complete -c wrknv -n "__fish_use_subcommand" -a "sync" -d "Install all tools"
complete -c wrknv -n "__fish_use_subcommand" -a "generate-env" -d "Generate env script"
complete -c wrknv -n "__fish_use_subcommand" -a "container" -d "Manage containers"
complete -c wrknv -n "__fish_use_subcommand" -a "profile" -d "Manage profiles"
complete -c wrknv -n "__fish_use_subcommand" -a "config" -d "Manage configuration"
complete -c wrknv -n "__fish_use_subcommand" -a "package" -d "Manage packages"

# Setup options
complete -c wrknv -n "__fish_seen_subcommand_from setup" -l init -d "Initialize workenv"
complete -c wrknv -n "__fish_seen_subcommand_from setup" -l shell-integration -d "Set up shell aliases"
complete -c wrknv -n "__fish_seen_subcommand_from setup" -l force -d "Force recreate"
complete -c wrknv -n "__fish_seen_subcommand_from setup" -l check -d "Check dependencies"
complete -c wrknv -n "__fish_seen_subcommand_from setup" -l completions -a "bash zsh fish" -d "Generate completions"
complete -c wrknv -n "__fish_seen_subcommand_from setup" -l install -d "Install completions"

# TF options
complete -c wrknv -n "__fish_seen_subcommand_from tf" -l latest -d "Install latest version"
complete -c wrknv -n "__fish_seen_subcommand_from tf" -l list -d "List versions"
complete -c wrknv -n "__fish_seen_subcommand_from tf" -l dry-run -d "Dry run"
complete -c wrknv -n "__fish_seen_subcommand_from tf" -l terraform -d "Use Terraform"

# Container subcommands
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "build" -d "Build image"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "start" -d "Start container"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "enter" -d "Enter container"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "stop" -d "Stop container"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "restart" -d "Restart container"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "status" -d "Show status"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "logs" -d "Show logs"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "clean" -d "Clean resources"
complete -c wrknv -n "__fish_seen_subcommand_from container; and not __fish_seen_subcommand_from build start enter stop restart status logs clean rebuild" -a "rebuild" -d "Rebuild from scratch"

# Profile subcommands
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "list" -d "List profiles"
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "save" -d "Save profile"
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "load" -d "Load profile"
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "show" -d "Show profile"
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "delete" -d "Delete profile"
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "export" -d "Export profile"
complete -c wrknv -n "__fish_seen_subcommand_from profile; and not __fish_seen_subcommand_from list save load show delete export import" -a "import" -d "Import profile"

# Config subcommands
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "show" -d "Show config"
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "edit" -d "Edit config"
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "validate" -d "Validate config"
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "init" -d "Initialize config"
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "get" -d "Get value"
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "set" -d "Set value"
complete -c wrknv -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from show edit validate init get set path" -a "path" -d "Show path"

# Package subcommands
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "build" -d "Build package"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "verify" -d "Verify package"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "keygen" -d "Generate keys"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "clean" -d "Clean cache"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "init" -d "Initialize provider"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "list" -d "List packages"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "info" -d "Show package info"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "sign" -d "Sign package"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "publish" -d "Publish package"
complete -c wrknv -n "__fish_seen_subcommand_from package; and not __fish_seen_subcommand_from build verify keygen clean init list info sign publish config" -a "config" -d "Show config"
"""


# 🧰🌍🔚
