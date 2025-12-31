import os
import sys

def test_env_check():
    """Write environment to file for debugging."""
    with open("/tmp/xdist_env_debug.txt", "w") as f:
        f.write("=== XDIST WORKER ENV CHECK ===\n")
        f.write(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'NOT SET')}\n")
        f.write(f"PATH: {os.environ.get('PATH', 'NOT SET')[:300]}\n")
        f.write(f"sys.prefix: {sys.prefix}\n")
        f.write(f"sys.executable: {sys.executable}\n")

        import site
        f.write(f"site-packages: {site.getsitepackages()}\n")

        # Check structlog config
        import structlog
        config = structlog.get_config()
        f.write(f"structlog processors count: {len(config.get('processors', []))}\n")
        f.write(f"structlog wrapper: {config.get('wrapper_class')}\n")
        f.write(f"structlog processors: {config.get('processors')}\n")
        f.write("=== END ===\n")
    assert True
