# Security Policy

## Supported Versions

The following table lists the project versions currently supported with security updates and patches:

| Version | Supported          | Security Patches |
| ------- | ------------------ | ---------------- |
| 1.x.x   | :white_check_mark: | Active           |
| < 1.0.0 | :x:                | EOL              |

---

## Reporting a Vulnerability

We take the security of **Travel AI Extractor** seriously. If you discover or suspect a security vulnerability, please follow our responsible disclosure process:

### Do NOT Open a Public GitHub Issue for Security Vulnerabilities

To report a vulnerability:
1. Email your report privately to **security@travelaiextractor.com** or submit a private security advisory through the [GitHub Security Advisory Tab](https://github.com/altafpasha/travel-aI-extractor/security/advisories/new).
2. Include a detailed description of the issue, proof of concept steps, affected components, and potential impact.

---

## Disclosure & Incident Response Process

- **Acknowledgement**: We will acknowledge receipt of your vulnerability report within **24 hours**.
- **Assessment**: Our DevSecOps team will assess the vulnerability and determine severity within **48 hours**.
- **Fix & Patch**: We will develop, test, and release a security patch within **7 business days** for High/Critical severity issues.
- **Public Disclosure**: Once patched, a public security advisory and release notes will be published acknowledging your contribution (unless requested to remain anonymous).

---

## DevSecOps Pipeline & Automated Scans

This repository enforces automated security quality gates on every commit and Pull Request:
- **Secret Scanning**: Gitleaks checks for committed API keys, tokens, and passwords.
- **Python SAST**: Bandit scans Python code for security flaws.
- **Dependency Audit**: `pip-audit` checks dependencies against known CVE databases.
- **Container Security**: Hadolint and Trivy scan Dockerfiles and container images.
- **SBOM**: Software Bill of Materials generated via Syft.
- **CodeQL**: Automated GitHub static code analysis.
