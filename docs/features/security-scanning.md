# Security Scanning

wrknv provides unified configuration for secret scanning tools, allowing you to define allowlists once and generate configuration files for multiple scanners.

## Supported Scanners

- **TruffleHog** - Offline git history scanning
- **Gitleaks** - Offline git leak detection
- **GitGuardian** - Cloud-based secret scanning (via ggshield)

## Configuration

Add security allowlist configuration to either `pyproject.toml` or `wrknv.toml`:

### pyproject.toml

```toml
[tool.security]
description = "Test fixtures and example credentials - intentionally committed"
allowed_paths = [
    "tests/certs/*.key",
    "tests/fixtures/crypto.py",
    "docs/**/*.md",
    "examples/**/*.key",
]
```

### wrknv.toml

```toml
[security]
description = "Test fixtures and example credentials"
allowed_paths = [
    "tests/certs/*.key",
    "docs/**/*.md",
]
```

## Commands

### Generate Configuration Files

Generate all scanner configuration files:

```bash
we security generate
```

Generate for a specific tool only:

```bash
we security generate --tool trufflehog
we security generate --tool gitleaks
we security generate --tool gitguardian
```

Preview what would be generated:

```bash
we security generate --dry-run
```

### Show Current Configuration

```bash
we security show
```

### Validate Configuration

```bash
we security validate
```

### Preview Generated Configs

```bash
we security preview
we security preview --tool gitleaks
```

### Run Scanners

Run all available scanners with the configured allowlists:

```bash
we security scan
```

Run a specific scanner:

```bash
we security scan --tool trufflehog
we security scan --tool gitleaks
```

Skip regenerating config files before scanning:

```bash
we security scan --no-generate
```

## Generated Files

The `security generate` command creates:

| File | Scanner |
|------|---------|
| `.trufflehog-exclude-paths.txt` | TruffleHog |
| `.gitleaks.toml` | Gitleaks |
| `.gitguardian.yaml` | GitGuardian |

## Glob Pattern Syntax

The `allowed_paths` field supports glob patterns:

| Pattern | Matches |
|---------|---------|
| `*.key` | Files ending in `.key` in current directory |
| `**/*.key` | Files ending in `.key` anywhere in tree |
| `tests/certs/*.key` | `.key` files in `tests/certs/` |
| `docs/**/*.md` | `.md` files anywhere under `docs/` |

## CI Integration

Add to your CI workflow:

```yaml
- name: Security Scan
  run: we security scan
```

Or run individual scanners:

```yaml
- name: TruffleHog Scan
  run: |
    we security generate
    trufflehog git file://. --fail --exclude-paths=.trufflehog-exclude-paths.txt

- name: Gitleaks Scan
  run: |
    we security generate
    gitleaks git . --config=.gitleaks.toml
```

## Task Integration

Add security tasks to your `wrknv.toml`:

```toml
[tasks.security]
_default = "we security.scan"
generate = "we security.generate"
trufflehog = "trufflehog git file://. --fail --exclude-paths=.trufflehog-exclude-paths.txt"
gitleaks = "gitleaks git . --config=.gitleaks.toml"
```

Then run with:

```bash
we security           # Runs _default (scan)
we security.generate  # Generate configs only
we security.trufflehog  # Run trufflehog directly
```
