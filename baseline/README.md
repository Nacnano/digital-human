# Project Setup

This project is setup with uv.
Refer to the root [README.md](../README.md) for more details.

---
## Vscode Setup
Select local `.venv` as the python interpreter (included `.ipynb` files)

### Formatter (black or ruff)
- Vscode [Ruff Formatter](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) (recommended)
- Vscode [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) and [isort](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)
---

## Adding/removing dependencies (`pip install` like)
```
uv add <package>
uv remove <package>
```

---

## Run python files
```bash
uv run <filename>.py
uv run python <filename>.py
```