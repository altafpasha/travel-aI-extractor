# Enterprise DevSecOps & CI/CD Pipeline Documentation

> Complete technical documentation for the enterprise-grade **DevSecOps**, **Security Pipeline**, and **Continuous Deployment** architecture powering **Travel AI Extractor**.

---

## 📖 Table of Contents

- [1. Architecture Overview](#1-architecture-overview)
- [2. Quality Gates & Security Controls](#2-quality-gates--security-controls)
- [3. Security Scanning Tools](#3-security-scanning-tools)
- [4. Container Security & Image Hardening](#4-container-security--image-hardening)
- [5. Software Bill of Materials (SBOM)](#5-software-bill-of-materials-sbom)
- [6. Container Image Signing (Cosign)](#6-container-image-signing-cosign)
- [7. Linux VPS Deployment Flow & Secrets](#7-linux-vps-deployment-flow--secrets)
- [8. Post-Deployment Health Check & Rollback](#8-post-deployment-health-check--rollback)
- [9. Dependency Management & Security Policy](#9-dependency-management--security-policy)

---

## 1. Architecture Overview

The DevSecOps pipeline enforces automated linting, security scanning, container hardening, SBOM generation, and zero-downtime deployment to a Linux VPS upon passing all quality gates.

```
                                  Git Push / Pull Request
                                             │
                                             ▼
                     ┌───────────────────────────────────────────────┐
                     │          GitHub Actions CI/CD Pipeline        │
                     └───────────────────────┬───────────────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             ▼                               ▼                               ▼
  ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
  │   CI Quality Job    │         │  Security Scan Job  │         │    CodeQL Analysis  │
  │    (ci.yml)         │         │   (security.yml)    │         │    (codeql.yml)     │
  └──────────┬──────────┘         └──────────┬──────────┘         └──────────┬──────────┘
             │                               │                               │
             │   Ruff, Black, isort,         │   Gitleaks, Bandit,           │   GitHub Static
             │   Pytest & Coverage           │   pip-audit, Hadolint,        │   Python Code Analysis
             │                               │   Trivy FS/Container          │
             └───────────────────────────────┼───────────────────────────────┘
                                             │
                                   ALL Quality Gates PASS
                                             │
                                             ▼
                                 ┌───────────────────────┐
                                 │ Continuous Deployment │
                                 │     (deploy.yml)      │
                                 └───────────┬───────────┘
                                             │
                                  SSH Deployment to VPS
                                             │
                                             ▼
                                 ┌───────────────────────┐
                                 │ Linux Production VPS  │
                                 │  docker compose pull  │
                                 │  docker compose up -d │
                                 └───────────┬───────────┘
                                             │
                                 ┌───────────▼───────────┐
                                 │  GET /health Check    │
                                 └───────────┬───────────┘
                                    ┌────────┴────────┐
                                 HTTP 200          HTTP 500
                                    │                 │
                             Deployment OK     Auto-Rollback
```

---

## 2. Quality Gates & Security Controls

Deployment to production is **strictly prohibited** if any of the following quality gate conditions occur:

1. ❌ Any Pytest unit or integration test fails.
2. ❌ Gitleaks detects any committed secret, token, password, or API key.
3. ❌ Bandit SAST scanner detects any **High** severity security flaw.
4. ❌ `pip-audit` detects any **Critical** dependency vulnerability.
5. ❌ Trivy scanner detects any **Critical** vulnerability in the repository filesystem or built Docker image.
6. ❌ Hadolint detects Dockerfile linting errors.
7. ❌ Production Docker image build fails.

---

## 3. Security Scanning Tools

| Tool | Category | Target | Failure Condition |
|---|---|---|---|
| **Gitleaks** | Secret Detection | Git commits & PRs | Any secret/token detected |
| **Bandit** | Python SAST | `app/` Python source code | High severity security flaws |
| **pip-audit** | Dependency Audit | `requirements.txt` | Critical CVE vulnerabilities |
| **Hadolint** | Docker Linter | `docker/Dockerfile` | Dockerfile best practice errors |
| **Trivy FS** | Filesystem Scan | Repo root | Critical vulnerabilities |
| **Trivy Container** | Image Scan | Built Docker container | Critical container vulnerabilities |
| **CodeQL** | Static Code Analysis | Python codebase | Extended security & quality alerts |

---

## 4. Container Security & Image Hardening

The production Docker image (`docker/Dockerfile`) enforces security best practices:

1. **Multi-Stage Build**: Separates heavy build tools (`build-essential`) from runtime dependencies to keep the final image minimal and reduce attack surface area.
2. **Dedicated Non-Root User**: Runs under `appuser` (UID 10001, GID 10001) instead of `root`.
3. **Embedded Health Check**:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
       CMD curl -f http://localhost:8000/health || exit 1
   ```
4. **Isolated Bridge Network (`travel_net`)**: Database and Redis ports are bound strictly to `127.0.0.1` inside `docker-compose.yml` to prevent public port exposure.
5. **Resource Limits**: Enforces CPU (`cpus: '2.0'`) and RAM (`memory: 2g`) caps per service.

---

## 5. Software Bill of Materials (SBOM)

The pipeline automatically generates Software Bill of Materials (SBOM) artifacts on every release/security run using **Syft**:
- **SPDX Format**: `sbom-spdx.json`
- **CycloneDX Format**: `sbom-cyclonedx.json`

Artifacts are archived in GitHub Actions build runs and retention-managed for 30 days for compliance audits.

---

## 6. Container Image Signing (Cosign)

Container image provenance and signing is prepared using **Sigstore Cosign**:

### Enabling Keyless OIDC Image Signing
When pushing images to GitHub Container Registry (`ghcr.io`):
```bash
cosign sign --yes ghcr.io/altafpasha/travel-ai-extractor:latest
```

### Verifying Image Signature
```bash
cosign verify ghcr.io/altafpasha/travel-ai-extractor:latest \
  --certificate-identity-regexp "https://github.com/altafpasha/travel-aI-extractor" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
```

---

## 7. Linux VPS Deployment Flow & Secrets

### Configured GitHub Secrets:
To enable automated deployments, configure the following secrets in **GitHub Repository Settings -> Secrets and variables -> Actions**:

- `VPS_HOST`: Public IP address or domain of the Linux VPS.
- `VPS_USERNAME`: SSH username (e.g. `ubuntu` or `deploy`).
- `VPS_SSH_KEY`: OpenSSH Private Key for passwordless SSH authentication.
- `VPS_PORT`: SSH Port (Default: `22`).
- `GEMINI_API_KEY`: Production Gemini 2.5 Flash API Key.
- `GOOGLE_PLACES_API_KEY`: Production Google Places API Key.

---

## 8. Post-Deployment Health Check & Rollback

### Automated Health Verification:
Immediately after executing `docker compose up -d` on the Linux VPS, the CD workflow polls `http://localhost:8000/health`:

```bash
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
```

### Automated Rollback Procedure:
If `HEALTH_STATUS` returns any code other than `200 OK`:
1. The deployment pipeline logs a failure alert.
2. Executes automatic rollback command: `docker compose rollback` (or restarts previous stable release).
3. Pipeline terminates with exit code `1`, blocking broken code from serving traffic.

---

## 9. Dependency Management & Security Policy

- **Dependabot (`.github/dependabot.yml`)**: Automated weekly dependency PRs for `pip` and `github-actions`.
- **Security Policy (`SECURITY.md`)**: Public security vulnerability reporting policy and disclosure timeline.
