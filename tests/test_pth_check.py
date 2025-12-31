import os
import sys

def test_pth_check():
    """Check if .pth file ran."""
    with open("/tmp/pth_debug.txt", "w") as f:
        # Check if testkit early init was imported
        f.write("=== PTH FILE CHECK ===\n")
        f.write(f"'provide.testkit._early_init' in sys.modules: {'provide.testkit._early_init' in sys.modules}\n")

        # Check what modules related to testkit are loaded
        testkit_modules = [m for m in sys.modules if 'testkit' in m]
        f.write(f"testkit modules: {testkit_modules}\n")

        # Check structlog config
        import structlog
        config = structlog.get_config()
        f.write(f"structlog processors: {len(config.get('processors', []))}\n")
        f.write(f"structlog wrapper: {config.get('wrapper_class')}\n")

        f.write("=== END ===\n")
    assert True
