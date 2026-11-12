# Contributing to Javo Agents

Thank you for contributing to Javo Agents!

## Development Setup

1. Clone the repository and copy `.env.example` to `.env`.
2. Install Python dependencies:
   ```bash
   cd services/local-runtime
   pip install -r requirements.txt
   ```
3. Run the test suite before submitting changes:
   ```bash
   cd services/local-runtime
   pytest ../../tests
   ```

## Coding Standards

- **Python**: Follow PEP 8, use type annotations (`from __future__ import annotations`), async I/O with SQLAlchemy 2.0 `Mapped` columns, and Pydantic v2 models.
- **Agents**: All specialist agents must inherit from `BaseAgent`, define explicit `capabilities` and `required_permissions`, and never bypass `PrivacyFirewall`.
- **Security**: Never commit `.env`, API keys, tokens, or database files.

## Pull Requests

1. Create a feature branch from `main`.
2. Add unit/integration tests covering your changes.
3. Ensure all tests and linters pass.
4. Submit a clear description referencing relevant issues.
