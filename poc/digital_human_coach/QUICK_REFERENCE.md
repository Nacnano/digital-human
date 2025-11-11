# Quick Reference - Refactored Structure

## 🎯 **Quick Commands**

### Verify Setup

```bash
python scripts/verify_setup.py
```

### Run Tests

```bash
# Direct
python tests/test_api_integration.py

# Pytest
pytest tests/

# With coverage
pytest --cov=app tests/
```

### Run Examples

```bash
python examples/conversation_example.py
```

### Show Status

```bash
python scripts/show_verification_summary.py
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📁 **File Locations**

| Old Location              | New Location                           | Purpose           |
| ------------------------- | -------------------------------------- | ----------------- |
| `test_integration.py`     | `tests/test_api_integration.py`        | Integration tests |
| `quick_test.py`           | `scripts/verify_setup.py`              | Environment check |
| `verification_summary.py` | `scripts/show_verification_summary.py` | Status display    |
| `examples/test_api.py`    | `examples/conversation_example.py`     | Usage example     |

## 🗂️ **Directory Structure**

```
digital_human_coach/
├── tests/               # Test suite
│   ├── test_api_integration.py
│   └── __init__.py
├── scripts/             # Utility scripts
│   ├── verify_setup.py
│   ├── show_verification_summary.py
│   └── __init__.py
├── examples/            # Usage examples
│   ├── conversation_example.py
│   └── sample_feedback.md
├── app/                 # Application code
├── docs/                # Documentation
└── [Docker files, configs, etc.]
```

## ✅ **What Changed**

- ✅ Tests moved to `tests/` directory
- ✅ Scripts moved to `scripts/` directory
- ✅ Examples cleaned up in `examples/`
- ✅ Redundant files removed
- ✅ README.md updated
- ✅ .dockerignore updated
- ✅ pytest-compatible test structure

## 🚀 **Benefits**

- Clean repository root
- Standard Python project layout
- Clear separation of concerns
- Easier to navigate
- pytest-compatible
- Docker-optimized
