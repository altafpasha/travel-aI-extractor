## 📝 Pull Request Summary

Provide a concise summary of the changes made and the motivation behind them.

---

## 🔍 Change Type

- [ ] 🐛 Bug Fix
- [ ] ✨ New Feature
- [ ] 🔒 Security Improvement / Patch
- [ ] 🚀 Performance Optimization
- [ ] 📚 Documentation Update
- [ ] ⚙️ CI/CD Pipeline Adjustment

---

## 🛡️ DevSecOps & Security Checklist

- [ ] **Tests**: Unit & Integration tests have been added/updated and pass locally (`pytest`).
- [ ] **Linting & Code Style**: Code complies with Ruff, Black formatting, and isort imports (`black --check .`).
- [ ] **Security SAST**: Run `bandit -r app/` with no High severity warnings.
- [ ] **Secrets Check**: No API keys, tokens, passwords, or `.env` files are included in this PR (`gitleaks`).
- [ ] **Dependencies**: No critical vulnerability added to `requirements.txt` (`pip-audit`).
- [ ] **Breaking Changes**: Are there any breaking API changes?
  - [ ] Yes (explain below)
  - [ ] No

---

## 🧪 Verification & Testing Executed

Describe how the changes were verified locally:
```bash
docker run --rm -v "${PWD}:/app" travel-ai-extractor:latest pytest -v
```

---

## 📸 Screenshots / Outputs (If Applicable)

Attach any relevant terminal test logs or API output screenshots.
