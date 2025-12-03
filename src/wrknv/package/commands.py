#
# wrknv/env/package/commands.py
#
"""
Package Commands Implementation
===============================
Command implementations for package management using flavorpack Python API.
"""

from pathlib import Path
import shutil
from typing import Any

from provide.foundation import logger

from wrknv.config import WorkenvConfig

from .manager import PackageManager


def _check_flavor_installed() -> None:
    """Check if flavorpack is installed."""
    try:
        import flavor
    except ImportError as e:
        raise ImportError("flavorpack not installed. Install it with: uv pip install flavorpack") from e


def build_package(
    manifest_path: Path, config: WorkenvConfig | None = None, dry_run: bool = False
) -> list[Path]:
    """Build a package from manifest file."""
    if dry_run:
        logger.info(f"[DRY-RUN] Would build package from {manifest_path}")
        return [manifest_path.parent / "dist" / "package.psp"]

    _check_flavor_installed()

    if config is None:
        config = WorkenvConfig()

    manager = PackageManager(config)

    # Check required tools
    tools = manager.check_required_tools()
    missing = {k: v for k, v in tools.items() if v is None}
    if missing:
        logger.warning(f"Missing required tools: {list(missing.keys())}")

    # Set up build environment (for environment variables)
    _env = manager.setup_build_environment()

    # Build using flavorpack Python API
    from flavor import build_package_from_manifest

    logger.info(f"Building package from {manifest_path}")

    try:
        packages = build_package_from_manifest(
            manifest_path=manifest_path,
            output_path=manifest_path.parent / "dist",
            show_progress=True,
        )
        logger.info(f"Successfully built {len(packages)} package(s)")
        return packages
    except Exception as e:
        logger.error(f"Build failed: {e}")
        raise RuntimeError(f"Package build failed: {e}") from e


def verify_package(package_path: Path, config: WorkenvConfig | None = None) -> dict[str, Any]:
    """Verify a package file."""
    _check_flavor_installed()

    from flavor import verify_package as flavor_verify

    logger.info(f"Verifying package: {package_path}")

    try:
        result = flavor_verify(package_path)
        logger.info("Package verification successful")
        return result
    except Exception as e:
        logger.error(f"Package verification failed: {e}")
        raise RuntimeError(f"Package verification failed: {e}") from e


def generate_keys(output_dir: Path, config: WorkenvConfig | None = None) -> tuple[Path, Path]:
    """Generate signing key pair."""
    _check_flavor_installed()

    from flavor.packaging import generate_key_pair

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating signing keys in {output_dir}")

    try:
        private_key, public_key = generate_key_pair(output_dir)
        logger.info(f"Generated key pair: {private_key.name}, {public_key.name}")
        return (private_key, public_key)
    except Exception as e:
        logger.error(f"Key generation failed: {e}")
        raise RuntimeError(f"Key generation failed: {e}") from e


def clean_cache(config: WorkenvConfig | None = None) -> None:
    """Clean package build cache."""
    _check_flavor_installed()

    from flavor import clean_cache as flavor_clean

    # Clean flavor cache
    logger.info("Cleaning flavor cache...")
    try:
        flavor_clean()
        logger.info("Flavor cache cleaned")
    except Exception as e:
        logger.warning(f"Failed to clean flavor cache: {e}")

    # Clean wrknv package cache
    if config is None:
        config = WorkenvConfig()
    manager = PackageManager(config)
    cache_dir = manager.get_package_cache_dir()
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)
        logger.info(f"Cleaned package cache at {cache_dir}")


def init_provider(project_dir: Path, config: WorkenvConfig | None = None) -> Path:
    """Initialize a new provider project."""
    # Basic project scaffolding
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create basic structure
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)
    (project_dir / "keys").mkdir(exist_ok=True)

    # Create basic pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "provider-example"
version = "0.1.0"
description = "Example Terraform provider"
requires-python = ">=3.11"

[tool.flavor]
provider_name = "example"
entry_point = "provider.main:serve"

[tool.flavor.signing]
private_key_path = "keys/private.pem"
public_key_path = "keys/public.pem"
"""
    )

    logger.info(f"Initialized provider project at {project_dir}")
    return project_dir


def list_packages(config: WorkenvConfig | None = None) -> list[dict[str, str]]:
    """List built packages."""
    if config is None:
        config = WorkenvConfig()

    manager = PackageManager(config)
    output_dir = manager.get_package_output_dir()

    packages = []
    if output_dir.exists():
        for psp_file in output_dir.glob("*.psp"):
            stat = psp_file.stat()
            packages.append(
                {
                    "name": psp_file.stem,
                    "version": "unknown",  # Would need to inspect package
                    "size": f"{stat.st_size / 1024 / 1024:.1f}MB",
                    "path": str(psp_file),
                }
            )

    return packages


def get_package_info(package_path: Path, config: WorkenvConfig | None = None) -> dict[str, Any]:
    """Get detailed information about a package."""
    _check_flavor_installed()

    from flavor import verify_package as flavor_verify

    logger.info(f"Inspecting package: {package_path}")

    try:
        # verify_package returns package metadata including verification info
        verification_result = flavor_verify(package_path)

        stat = package_path.stat()
        return {
            "name": package_path.stem,
            "size": f"{stat.st_size / 1024 / 1024:.1f}MB",
            "path": str(package_path),
            "verification": verification_result,
        }
    except Exception as e:
        logger.error(f"Package inspection failed: {e}")
        raise RuntimeError(f"Package inspection failed: {e}") from e


def sign_package(package_path: Path, key_path: Path, config: WorkenvConfig | None = None) -> None:
    """Sign an existing package."""
    # Flavor packages are signed during the pack process
    logger.info("Package signing is done during build with signing keys")
    logger.info(f"To sign {package_path}, rebuild with signing keys configured")
    raise NotImplementedError(
        "Package signing is performed during build. "
        "Use 'wrknv package build' with signing keys configured in pyproject.toml"
    )


def publish_package(package_path: Path, registry: str, config: WorkenvConfig | None = None) -> dict[str, str]:
    """Publish package to a registry."""
    # This would need a registry client implementation
    logger.info(f"Publishing {package_path} to {registry}")

    # For now, return mock data
    # TODO: Implement actual registry publishing
    return {
        "url": f"https://{registry}.example.com/{package_path.stem}",
        "sha256": "abc123def456",  # Would calculate real hash
        "status": "mock",
    }


# 🧰🌍🖥️🪄
